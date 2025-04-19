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
import subprocess
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
        self.last_update_check = time.time()  # Nueva variable para control de actualizaciones
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

            prompt = """
            Eres un asistente de monitoreo para adultos mayores. Analiza esta imagen de la cámara de seguridad donde pueden aparecer:
            - "Mamita María" (abuela)
            - "Papito Jorge" (abuelo)
            
            Por favor proporciona:
            
            1. DESCRIPCIÓN: Describe detalladamente la escena, quién aparece, qué están haciendo, y cualquier objeto o situación relevante.
            
            2. ACTIVIDAD: Identifica si están realizando alguna actividad de su rutina diaria como:
               - Comiendo
               - Caminando
               - Descansando
               - Viendo televisión
               - Recibiendo visitas
               - Tomando medicamentos
               - Otra actividad (especificar)
            
            3. NIVEL DE RIESGO: Clasifica la situación en una escala de 1 a 5:
               - Nivel 1: Normal, sin riesgos aparentes
               - Nivel 2: Atención leve (posible situación a monitorear)
               - Nivel 3: Precaución (situación que requiere verificación)
               - Nivel 4: Alerta (posible situación de riesgo)
               - Nivel 5: Emergencia (situación crítica que requiere intervención inmediata)
            
            4. JUSTIFICACIÓN: Explica brevemente por qué asignaste ese nivel de riesgo.
            
            Responde con estos cuatro apartados claramente separados.
            """

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente especializado en monitoreo de adultos mayores, enfocado en seguridad y bienestar."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
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
                    "analysis": analysis_result['choices'][0]['message']['content'],
                    "raw_response": analysis_result  # Opcional: guardar respuesta completa
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
            
    def check_for_updates(self):
        """Verifica y aplica actualizaciones desde GitHub"""
        try:
            logging.info("Verificando actualizaciones desde GitHub...")
            
            # Verificar si hay cambios en el repositorio
            result = subprocess.run(['git', 'fetch'], capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Error al verificar actualizaciones: {result.stderr}")
                return
                
            # Verificar si hay commits nuevos
            result = subprocess.run(['git', 'rev-list', 'HEAD..origin/main', '--count'], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip() != '0':
                logging.info(f"Se encontraron {result.stdout.strip()} commits nuevos")
                
                # Guardar logs antes de actualizar
                logging.info("Aplicando actualizaciones...")
                
                # Realizar pull
                result = subprocess.run(['git', 'pull', 'origin', 'main'], 
                                       capture_output=True, text=True)
                
                if result.returncode == 0:
                    logging.info("Actualización exitosa. Reiniciando servicio...")
                    
                    # Notificar al administrador
                    self.notify_admin("Sistema actualizado automáticamente. Reiniciando servicio.")
                    
                    # Reiniciar el servicio
                    subprocess.run(['sudo', 'systemctl', 'restart', 'familysafe'])
                    
                    # No es necesario hacer más, el servicio se reiniciará
                    sys.exit(0)
                else:
                    logging.error(f"Error al actualizar: {result.stderr}")
            else:
                logging.info("No hay actualizaciones disponibles")
                
        except Exception as e:
            logging.error(f"Error verificando actualizaciones: {e}")

    def monitor_loop(self):
        """Loop principal mejorado con actualizaciones automáticas"""
        while self.running:
            try:
                current_time = time.time()
                
                # Health check periódico
                if (current_time - self.last_health_check) >= MONITORING_CONFIG['health_check_interval']:
                    self.check_system_health()
                    self.last_health_check = current_time
                
                # Verificación de actualizaciones (cada 24 horas por defecto)
                update_interval = MONITORING_CONFIG.get('update_check_interval', 86400)  # 24 horas en segundos
                if (current_time - self.last_update_check) >= update_interval:
                    self.check_for_updates()
                    self.last_update_check = current_time
                
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
    
    # Verificar actualizaciones al inicio
    logging.info("Verificando actualizaciones al inicio...")
    monitor.check_for_updates()
    
    # Continuar con el loop normal
    monitor.monitor_loop()

if __name__ == "__main__":
    setup_logging()
    main() 