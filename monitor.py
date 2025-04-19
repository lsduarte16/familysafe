#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import cv2
import base64
import requests
import json
from datetime import datetime, timezone
import time
import tempfile
import logging
from pymongo import MongoClient
import sys
from config import CAMERAS_CONFIG, MONITORING_CONFIG, SYSTEM_CONFIG, NOTIFICATION_CONFIG
import signal
import psutil
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configura sistema de logs"""
    log_config = SYSTEM_CONFIG['logs']
    
    # Crear directorio de logs si no existe
    log_dir = os.path.dirname(log_config['main_log'])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, mode=0o755)

    # Configurar handler principal
    main_handler = RotatingFileHandler(
        log_config['main_log'],
        maxBytes=log_config['max_size'],
        backupCount=log_config['backup_count']
    )

    # Configurar handler de errores
    error_handler = RotatingFileHandler(
        log_config['error_log'],
        maxBytes=log_config['max_size'],
        backupCount=log_config['backup_count']
    )
    error_handler.setLevel(logging.ERROR)

    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(log_config['log_level']))
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)

class Monitor:
    def __init__(self):
        self.load_environment()
        self.setup_mongodb()
        self.setup_cameras()
        self.last_health_check = time.time()
        self.running = True
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
    def load_environment(self):
        """Carga variables de entorno"""
        load_dotenv()
        self.openai_endpoint = os.getenv('AZURE_ENDPOINT')
        self.openai_key = os.getenv('API_KEY')
        self.deployment_name = os.getenv('CHAT_DEPLOYMENT')
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.mongodb_db = os.getenv('MONGODB_DB_NAME')

    def setup_mongodb(self):
        """Configura conexión MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.mongodb_db]
            self.collection = self.db.monitoreo
            logging.info("Conexión a MongoDB establecida")
        except Exception as e:
            logging.error(f"Error conectando a MongoDB: {e}")
            sys.exit(1)

    def setup_cameras(self):
        """Configura las cámaras"""
        self.cameras = {}
        for cam_id, config in CAMERAS_CONFIG.items():
            stream_url = config['stream_url'].format(
                user=config['user'],
                password=config['password'],
                ip=config['ip']
            )
            self.cameras[cam_id] = {
                'name': config['name'],
                'stream_url': stream_url
            }
        logging.info(f"Cámaras configuradas: {len(self.cameras)}")

    def capture_image(self, camera_id):
        """Captura imagen de una cámara"""
        camera = self.cameras[camera_id]
        cap = cv2.VideoCapture(camera['stream_url'])
        
        if not cap.isOpened():
            logging.error(f"No se pudo acceder a {camera['name']}")
            return None
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            cv2.imwrite(temp_file.name, frame)
            return temp_file.name
        return None

    def get_cpu_temperature(self):
        """Obtiene temperatura CPU"""
        try:
            temp = psutil.sensors_temperatures()
            if 'coretemp' in temp:
                return temp['coretemp'][0].current
            return 0
        except:
            return 0

    def notify_admin(self, message):
        """Envía notificaciones según configuración"""
        if not NOTIFICATION_CONFIG['enabled']:
            return

        if NOTIFICATION_CONFIG['telegram_enabled']:
            self.send_telegram_notification(message)
        
        if NOTIFICATION_CONFIG['email_enabled']:
            self.send_email_notification(message)

    def analyze_with_gpt4v(self, image_path, camera_name):
        """Analiza imagen con GPT-4V"""
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            headers = {
                "api-key": self.openai_key,
                "Content-Type": "application/json"
            }

            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "¿Qué ves en esta imagen? Detecta personas, objetos o situaciones anormales."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                f"{self.openai_endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version=2024-02-15-preview",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                analysis_result = response.json()
                return {
                    "timestamp": datetime.now(timezone.utc),
                    "camera": camera_name,
                    "analysis": analysis_result['choices'][0]['message']['content']
                }
            else:
                logging.error(f"Error en API GPT-4V: {response.status_code}")
                return None

        except Exception as e:
            logging.error(f"Error en análisis GPT-4V: {e}")
            return None

    def handle_shutdown(self, signum, frame):
        """Manejo graceful de shutdown"""
        logging.info("Iniciando shutdown...")
        self.running = False
        if hasattr(self, 'client'):
            self.client.close()
        sys.exit(0)

    def check_system_health(self):
        """Verificación de salud del sistema"""
        try:
            # Verificar temperatura CPU
            temp = self.get_cpu_temperature()
            if temp > SYSTEM_CONFIG['temp_threshold']:
                logging.warning(f"Temperatura CPU alta: {temp}°C")
                self.notify_admin(f"Alerta: Temperatura CPU {temp}°C")
            
            # Verificar espacio en disco
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                logging.warning(f"Espacio en disco bajo: {disk.percent}%")
                self.notify_admin("Alerta: Espacio en disco bajo")

        except Exception as e:
            logging.error(f"Error en health check: {e}")

    def monitor_loop(self):
        """Loop principal mejorado"""
        while self.running:
            try:
                current_time = time.time()
                
                # Health check periódico
                if (current_time - self.last_health_check) >= MONITORING_CONFIG['health_check_interval']:
                    self.check_system_health()
                    self.last_health_check = current_time
                
                for camera_id in self.cameras:
                    image_path = self.capture_image(camera_id)
                    if image_path:
                        try:
                            analysis = self.analyze_with_gpt4v(
                                image_path, 
                                self.cameras[camera_id]['name']
                            )
                            if analysis:
                                self.collection.insert_one(analysis)
                                logging.info(f"Registro guardado para {self.cameras[camera_id]['name']}")
                        finally:
                            if os.path.exists(image_path):
                                os.remove(image_path)
                
                time.sleep(MONITORING_CONFIG['interval'])
                
            except Exception as e:
                logging.error(f"Error en ciclo de monitoreo: {e}")
                time.sleep(MONITORING_CONFIG['retry_delay'])

def main():
    monitor = Monitor()
    monitor.monitor_loop()

if __name__ == "__main__":
    setup_logging()
    main() 