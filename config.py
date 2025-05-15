import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = "7669832528:AAGteaJ2OrH2Jv5PNyPBEE3XD-tbZ7pV3xI"

# Admin IDs
ADMIN_IDS = [396869465]  # Замініть на ваш Telegram ID

# Group Chat ID
GROUP_CHAT_ID = -4757435492

# Training Types
TRAINING_TYPES = [
    "TRX",
    "Power",
    "Tabata",
    "Circuit training",
    "Power Stretching",
    "Stretching",
    "Stretching+прес",
    "HIIT",
    "Step aerobic",
    "Outdoor training",
    "Functional training"
]

# Налаштування бази даних
DATABASE_URL = "sqlite:///fitness_studio.db" 