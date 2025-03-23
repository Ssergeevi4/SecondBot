# config/config.py
from dotenv import load_dotenv
import os

# Загружаем .env из корня проекта
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

TOKEN = os.getenv("TOKEN")
SHEET_NAME = os.getenv("SHEET_NAME")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")
LIMIT = int(os.getenv("LIMIT"))
