# backend/core/config.py

import os
import yaml
from typing import Dict
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

class ProjectSettings:
    def __init__(self):
        self.PROJECT_NAME = "Herobot"
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ALLOW_ORIGINS = ["http://localhost:8080", "http://172.30.1.88:8080/"]
        self.HOST = "127.0.0.1"
        self.PORT = 5001
        self.RELOAD = True

class APISettings:
    def __init__(self):
        self.X_RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY")
        self.X_RAPIDAPI_HOST = os.getenv("X_RAPIDAPI_HOST")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
        self.LANGCHAIN_SYSTEM_PROMPT_NAME = os.getenv("LANGCHAIN_INTENT_PROMPT_NAME")
        self.LANGCHAIN_FLIGHT_PROMPT_NAME = os.getenv("LANGCHAIN_FLIGHT_PROMPT_NAME")
        self.AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
        self.AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

class DatabaseSettings:
    def __init__(self):
        self.ROOT_DIR = os.getenv("ROOT_DIR")
        db_config_path = os.path.join(self.ROOT_DIR, os.getenv("DB_CONFIG_PATH"))
        self.DB_CONFIG = self.load_db_config(db_config_path)['mysql']
        self.CONNECTION_STRING = self.make_connection_string(self.DB_CONFIG)
        self.SQLITE_CONNECTION_STRING = os.getenv("SQLITE_CONNECTION_STRING")

    def load_db_config(self, config_path='db_config.yaml') -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def make_connection_string(self, config: Dict) -> str:
        return URL.create(**config)

class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.project_settings = ProjectSettings()
        self.api_settings = APISettings()
        self.database_settings = DatabaseSettings()
        # 노출할 속성들
        self._expose_attributes()

    def _expose_attributes(self):
        for settings in (self.project_settings, self.api_settings, self.database_settings):
            for attr, value in settings.__dict__.items():
                setattr(self, attr, value)

class LLMConfig:
    CHAIN_TYPE_FLIGHT = "flight"
    CHAIN_TYPE_INTENT = "intent"
    CHAIN_TYPE_MESSAGE = "message"

settings = Settings()

if __name__ == "__main__":
    settings = Settings()
    print(settings.PROJECT_NAME)
    print(settings.OPENAI_API_KEY)
    print(settings.CONNECTION_STRING)
