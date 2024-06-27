# backend/core/config.py
import os
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
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
        self.AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
        self.AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ROOT_DIR = os.getenv("ROOT_DIR")
        self.DB_CONFIG_PATH = os.getenv("DB_CONFIG_PATH")
        self.ALLOW_ORIGINS = ["*"]
        self.HOST = "127.0.0.1"
        self.PORT = 5001
        self.RELOAD = True

settings = Settings()
