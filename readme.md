# FamilySafe - Sistema de Monitoreo con Cámaras

Sistema de monitoreo inteligente que utiliza cámaras IP y análisis de video con GPT-4V para la vigilancia y seguridad familiar.

## 🚀 Características

- Monitoreo en tiempo real de múltiples cámaras IP
- Análisis de video con GPT-4V
- Detección automática de eventos
- Sistema de alertas y notificaciones
- Almacenamiento en MongoDB
- Monitoreo de salud del sistema

## 📋 Requisitos Previos

- Python 3.8 o superior
- OpenCV
- MongoDB
- Conexión a Internet
- Cámaras IP compatibles con RTSP

## 🔧 Instalación

1. Clonar el repositorio:

bash
git clone https://github.com/lsduarte16/familysafe.git
cd familysafe

2. Configurar el entorno:

Crear archivo .env basado en el ejemplo
cp .env.example .env

Editar .env con tus credenciales
nano .env

3. Ejecutar el script de instalación:

bash
python3 setup.py

## ⚙️ Configuración

### Configuración de Cámaras
Editar `config.py` para agregar o modificar cámaras:

python
CAMERAS_CONFIG = {
    "cam1": {
        "name": "Cámara 1",
        "ip": "192.168.1.100",
        "user": "admin",
        "password": "password",
        "type": "hikvision",
        "stream_url": "rtsp://{user}:{password}@{ip}:554/Streaming/Channels/101"
    }
}

### Configuración del Sistema
Ajustar parámetros en `config.py`:
- Intervalos de monitoreo
- Umbrales de temperatura
- Configuración de logs
- Parámetros de notificaciones

## 🚀 Uso

### Servicio Systemd
El sistema se ejecuta como servicio:

bash
sudo systemctl start familysafe

Detener servicio
sudo systemctl stop familysafe

Ver estado
sudo systemctl status familysafe

Ver logs
journalctl -u familysafe


### Ejecución Manual
bash
python3 monitor.py


## 📊 Monitoreo y Logs

- Logs principales: `logs/monitor.log`
- Estado del sistema: `systemctl status monitor`
- Métricas de MongoDB: Accesibles via MongoDB Atlas

## 🔒 Seguridad

- Todas las credenciales deben estar en `.env`
- No compartir el archivo `.env`
- Mantener actualizadas las dependencias
- Revisar periódicamente los logs

## 🛠️ Troubleshooting

### Problemas Comunes

1. Cámara no accesible:
   - Verificar conexión de red
   - Confirmar credenciales
   - Comprobar URL de stream

2. Error de MongoDB:
   - Verificar conexión a internet
   - Confirmar credenciales en `.env`
   - Comprobar estado de MongoDB Atlas

3. Problemas de CPU/Memoria:
   - Revisar logs del sistema
   - Ajustar intervalos de monitoreo
   - Verificar espacio en disco

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para detalles

## 👥 Contribuir

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📞 Soporte

Para soporte y consultas:
- Crear un issue en GitHub
- Contactar al equipo de desarrollo

---
Desarrollado con ❤️ por LSduarte