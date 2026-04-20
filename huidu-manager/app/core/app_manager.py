import os
import logging
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Se python-dotenv non c'è, proviamo a parsare .env grezzo se esiste nella root
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

from app.api.huidu_client import HuiduClient
from app.api.device_api import DeviceApi
from app.api.program_api import ProgramApi
from app.api.file_api import FileApi
from app.core.file_uploader import FileUploader
from app.core.screen_manager import ScreenManager
from app.core.db import DatabaseManager

logger = logging.getLogger(__name__)

class AppManager:
    """Entry point unificato per i layer backend (API, Device, File, Programmi, DB)."""
    
    def __init__(self):
        # Preferiamo configurazioni da file ambiente
        host = os.environ.get("HUIDU_GATEWAY_HOST", "127.0.0.1")
        port = int(os.environ.get("HUIDU_GATEWAY_PORT", "30080"))
        sdk_key = os.environ.get("HUIDU_SDK_KEY", "")
        sdk_secret = os.environ.get("HUIDU_SDK_SECRET", "")
        
        logger.info(f"Inizializzazione AppManager -> Huidu Gateway at {host}:{port}")
        
        # 1. Base HTTP Client
        self.gateway = HuiduClient(
            host=host,
            port=port,
            sdk_key=sdk_key,
            sdk_secret=sdk_secret,
        )
        
        # 2. API Specifiche
        self.device_api = DeviceApi(self.gateway)
        self.file_api = FileApi(self.gateway)
        self.programs_api = ProgramApi(self.gateway)
        
        # 3. Manager Alto Livello
        self.screens = ScreenManager(self.device_api)
        self.uploader = FileUploader(self.file_api)
        self.db = DatabaseManager()
