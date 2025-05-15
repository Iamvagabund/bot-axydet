import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Admin IDs
ADMIN_IDS = [YOUR_TELEGRAM_ID]  # Replace with your Telegram ID

# Group Chat ID
GROUP_CHAT_ID = YOUR_GROUP_CHAT_ID

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