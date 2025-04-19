# Configuración de cámaras
CAMERAS_CONFIG = {
    "camera1": {
        "name": "Cámara Patio",
        "ip": "192.168.1.X",
        "user": "admin",
        "password": "password",
        "type": "hikvision",
        "stream_url": "rtsp://{user}:{password}@{ip}:554/Streaming/Channels/101"
    },
    "camera2": {
        "name": "Cámara Living",
        "ip": "192.168.1.Y",
        "user": "admin",
        "password": "password",
        "type": "hikvision",
        "stream_url": "rtsp://{user}:{password}@{ip}:554/Streaming/Channels/101"
    }
}

# Configuración de monitoreo
MONITORING_CONFIG = {
    "interval": 30,  # segundos entre capturas
    "max_retries": 3,  # intentos de reconexión
    "retry_delay": 5,  # segundos entre reintentos
    "health_check_interval": 300  # segundos entre chequeos de salud
}

# Configuración de sistema
SYSTEM_CONFIG = {
    "temp_threshold": 70,  # temperatura máxima CPU
    "log_file": "monitor.log",
    "log_level": "INFO",  # nuevo: nivel de logging configurable
    "github_repo": "https://github.com/lsduarte16/familysafe.git",
    "branch": "main",
    "health_check_enabled": True,  # nuevo: toggle para health checks
    "logs": {
        "main_log": "/var/log/familysafe/monitor.log",
        "error_log": "/var/log/familysafe/error.log",
        "access_log": "/var/log/familysafe/access.log",
        "max_size": 10485760,  # 10MB
        "backup_count": 5,
        "log_level": "INFO",
        "rotation": "daily"
    }
}

# Configuración de notificaciones
NOTIFICATION_CONFIG = {
    "enabled": True,
    "telegram_enabled": False,
    "email_enabled": True,
    "notification_threshold": "WARNING",
    "email_config": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "your-email@gmail.com",
        "admin_email": "admin@example.com"
    },
    "telegram_config": {
        "bot_token": "",
        "chat_id": ""
    }
} 