# config/config.py
from dotenv import load_dotenv
import os

# Загружаем .env из корня проекта
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

TOKEN = os.getenv("TOKEN")
SHEET_NAME = os.getenv("SHEET_NAME")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")
limit_str = os.getenv("LIMIT", "7")
LIMIT = int(limit_str) if limit_str else 7
# LIMIT = int(os.getenv("LIMIT", "7"))
