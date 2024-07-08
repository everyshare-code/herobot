# backend/core/config.py
import os
import yaml
from typing import Dict
from sqlalchemy import URL
from dotenv import load_dotenv
load_dotenv()
class Settings:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    def _initialize(self):
        self.PROJECT_NAME = "Herobot"
        self.X_RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY")
        self.X_RAPIDAPI_HOST = os.getenv("X_RAPIDAPI_HOST")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
        self.LANGCHAIN_PROMPT_NAME = os.getenv("LANGCHAIN_PROMPT_NAME")
        self.AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
        self.AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ROOT_DIR = os.getenv("ROOT_DIR")
        db_config_path = os.path.join(self.ROOT_DIR, os.getenv("DB_CONFIG_PATH"))
        self.DB_CONFIG = self.load_db_config(db_config_path)['mysql']
        self.CONNECTION_STRING = self.make_connection_string(self.DB_CONFIG)
        self.SQLITE_CONNECTION_STRING = os.getenv("SQLITE_CONNECTION_STRING")
        self.ALLOW_ORIGINS = ["http://localhost:8080", "http://172.30.1.88:8080/"]
        self.HOST = "127.0.0.1"
        self.PORT = 5001
        self.RELOAD = True
    def load_db_config(self, config_path='db_config.yaml') -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    def make_connection_string(self, config: Dict):
        return URL.create(**config)


settings = Settings()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    settings = Settings()
