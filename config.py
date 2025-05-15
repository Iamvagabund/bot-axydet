import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set")

admin_ids_str = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(id) for id in admin_ids_str.split(',') if id.strip()]

group_chat_id_str = os.getenv('GROUP_CHAT_ID')
if group_chat_id_str:
    GROUP_CHAT_ID = int(group_chat_id_str)
else:
    GROUP_CHAT_ID = None

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
