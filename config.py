# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Тестовые ключи ЮKassa
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")      # test_shop_...
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY") # test_...

WEBHOOK_HOST = "https://kaind0to-tg-pay-bot.hf.space"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"