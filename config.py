import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = "8199714639:AAGphA17RHFHIutHTzB3xQ6-wuhvhDtekRM"

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
    "Functional training",
    "Персональне тренування"
]

# Налаштування бази даних
DATABASE_URL = "sqlite:///fitness_studio.db" 