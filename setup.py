#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from config import SYSTEM_CONFIG

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def check_requirements():
    """Verifica requisitos del sistema"""
    required_packages = [
        'python3-opencv',
        'python3-pip',
        'git'
    ]
    
    logging.info("Verificando requisitos del sistema...")
    for package in required_packages:
        result = subprocess.run(['dpkg', '-s', package], capture_output=True)
        if result.returncode != 0:
            logging.info(f"Instalando {package}...")
            subprocess.run(['sudo', 'apt-get', 'install', '-y', package])

def setup_python_packages():
    """Instala paquetes Python necesarios"""
    requirements = [
        'python-dotenv>=0.19.0',
        'requests>=2.26.0',
        'pymongo>=3.12.0',
        'opencv-python>=4.5.0',
        'psutil>=5.8.0',
        'python-telegram-bot',
        'pytest'
    ]
    
    logging.info("Instalando paquetes Python...")
    for package in requirements:
        subprocess.run(['pip3', 'install', package])

def update_from_github():
    """Actualiza código desde GitHub"""
    repo_url = SYSTEM_CONFIG['github_repo']
    branch = SYSTEM_CONFIG['branch']
    
    if not os.path.exists('.git'):
        logging.info("Clonando repositorio...")
        subprocess.run(['git', 'clone', repo_url, '.'])
    
    logging.info("Actualizando desde GitHub...")
    subprocess.run(['git', 'fetch', 'origin'])
    subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'])

def setup_service():
    """Configura servicio systemd"""
    service_content = f"""[Unit]
Description=familysafe Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 {os.path.abspath('monitor.py')}
WorkingDirectory={os.getcwd()}
User={os.getenv('USER')}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_path = '/etc/systemd/system/familysafe.service'
    with open('familysafe.service', 'w') as f:
        f.write(service_content)
    
    subprocess.run(['sudo', 'mv', 'familysafe.service', service_path])
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'])
    subprocess.run(['sudo', 'systemctl', 'enable', 'familysafe'])
    subprocess.run(['sudo', 'systemctl', 'start', 'familysafe'])

def check_environment():
    """Verifica variables de entorno requeridas"""
    required_vars = [
        'AZURE_ENDPOINT',
        'API_KEY',
        'MONGODB_URI',
        'MONGODB_DB_NAME'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logging.error(f"Faltan variables de entorno: {', '.join(missing)}")
        sys.exit(1)

def setup_security():
    """Configura permisos y seguridad básica"""
    try:
        # Asegurar permisos del archivo .env
        if os.path.exists('.env'):
            os.chmod('.env', 0o600)
        
        # Asegurar permisos del directorio de logs
        log_dir = os.path.dirname(SYSTEM_CONFIG['logs']['main_log'])
        
        # Si no hay directorio, usar uno por defecto
        if not log_dir:
            log_dir = os.path.join(os.getcwd(), "logs")
            
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o755)
            
        # Verificar permisos de escritura
        if not os.access(log_dir, os.W_OK):
            logging.error(f"No hay permisos de escritura en {log_dir}")
            sys.exit(1)
            
        logging.info(f"Directorio de logs configurado: {log_dir}")
    except Exception as e:
        logging.error(f"Error configurando seguridad: {e}")
        sys.exit(1)

def setup_logging_dir():
    """Configura directorio de logs"""
    log_dir = "/var/log/familysafe"
    if not os.path.exists(log_dir):
        subprocess.run(['sudo', 'mkdir', '-p', log_dir])
        subprocess.run(['sudo', 'chown', f"{os.getenv('USER')}:", log_dir])
        subprocess.run(['sudo', 'chmod', '755', log_dir])
    logging.info(f"Directorio de logs creado: {log_dir}")

def main():
    setup_logging()
    check_environment()
    setup_security()
    check_requirements()
    setup_python_packages()
    update_from_github()
    setup_service()
    setup_logging_dir()
    logging.info("Instalación completada!")

if __name__ == "__main__":
    main() 