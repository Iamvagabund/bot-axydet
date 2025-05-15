import asyncio
from telegram import Bot
from config import TELEGRAM_TOKEN

async def delete_webhook():
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.delete_webhook()
    print("Вебхук успішно видалено")

if __name__ == "__main__":
    asyncio.run(delete_webhook()) 