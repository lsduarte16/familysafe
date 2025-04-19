# Configuración de cámaras
CAMERAS_CONFIG = {
    "camera1": {
        "name": "Cámara living",
        "ip": "192.168.100.35",
        "user": "admin",
        "password": "admin",
        "type": "hikvision",
        "stream_url": "rtsp://{user}:{password}@{ip}:554/h264/ch1/main/av_stream"
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
    "github_repo": "https://github.com/lsduarte16/familysafe.git",
    "branch": "main",
    "health_check_enabled": True,  # nuevo: toggle para health checks
    "logs": {
        "main_log": "logs/monitor.log",  # Ruta relativa
        "error_log": "logs/error.log",   # Ruta relativa
        "access_log": "logs/access.log", # Ruta relativa
        "max_size": 10485760,            # 10MB
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