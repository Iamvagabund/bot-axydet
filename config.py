import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))

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
