from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
print("DEBUG: Importing admin_handlers...")
import admin_handlers
print("DEBUG: Importing client_handlers...")
import client_handlers
print("DEBUG: Importing logging...")
import logging
from telegram import BotCommand
from telegram.error import TimedOut, NetworkError, Conflict
import asyncio

# Налаштовуємо логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Функція для обробки помилок
async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Виникла помилка. Спробуйте ще раз або зверніться до адміністратора."
        )

# Налаштовуємо меню команд
async def setup_commands():
    commands = [
        BotCommand("start", "Запустити бота"),
        BotCommand("admin", "Адмін-панель"),
    ]
    await application.bot.set_my_commands(commands)

# Створюємо бота з налаштуваннями
application = (
    Application.builder()
    .token(TELEGRAM_TOKEN)
    .read_timeout(30)
    .write_timeout(30)
    .connect_timeout(30)
    .pool_timeout(30)
    .build()
)

# Додаємо обробник помилок
application.add_error_handler(error_handler)

# Адмін-меню
application.add_handler(CommandHandler("admin", admin_handlers.admin_menu))
application.add_handler(CallbackQueryHandler(admin_handlers.admin_menu, pattern="^admin_menu$"))
application.add_handler(CallbackQueryHandler(admin_handlers.show_admin_schedule, pattern="^admin_schedule$"))
application.add_handler(CallbackQueryHandler(admin_handlers.show_day_schedule, pattern="^admin_day_"))
application.add_handler(CallbackQueryHandler(admin_handlers.add_training_menu, pattern="^admin_add_training$"))
application.add_handler(CallbackQueryHandler(admin_handlers.edit_training_menu, pattern="^admin_edit_training$"))
application.add_handler(CallbackQueryHandler(admin_handlers.show_users, pattern="^admin_users$"))
application.add_handler(CallbackQueryHandler(admin_handlers.show_tomorrow_trainings, pattern="^admin_tomorrow$"))

# Управление пользователями
application.add_handler(CallbackQueryHandler(admin_handlers.user_management, pattern="^user_management_"))
application.add_handler(CallbackQueryHandler(admin_handlers.add_paid_trainings, pattern="^add_paid_trainings_"))
application.add_handler(CallbackQueryHandler(admin_handlers.handle_add_package, pattern="^add_package_"))
application.add_handler(CallbackQueryHandler(admin_handlers.change_name_start, pattern="^change_name_start_"))
application.add_handler(CallbackQueryHandler(admin_handlers.change_name, pattern="^change_name_"))

# Додавання тренування
application.add_handler(CallbackQueryHandler(admin_handlers.add_training_time, pattern="^add_training_"))
application.add_handler(CallbackQueryHandler(admin_handlers.add_training_type, pattern="^add_time_"))
application.add_handler(CallbackQueryHandler(admin_handlers.save_training, pattern="^add_type_"))

# Перегляд і редагування тренувань
application.add_handler(CallbackQueryHandler(admin_handlers.view_existing_training, pattern="^view_existing_"))
application.add_handler(CallbackQueryHandler(admin_handlers.view_day_trainings, pattern="^view_trainings_"))
application.add_handler(CallbackQueryHandler(admin_handlers.edit_existing_training, pattern="^edit_existing_training_"))
application.add_handler(CallbackQueryHandler(admin_handlers.change_training_type, pattern="^change_type_"))

# Редагування тренувань
application.add_handler(CallbackQueryHandler(admin_handlers.edit_day_trainings, pattern="^edit_day_"))
application.add_handler(CallbackQueryHandler(admin_handlers.edit_training, pattern="^edit_training_"))
application.add_handler(CallbackQueryHandler(admin_handlers.delete_training, pattern="^delete_training_"))

# Реєструємо обробники для клієнтів
application.add_handler(CommandHandler("start", client_handlers.start))
application.add_handler(CallbackQueryHandler(client_handlers.show_client_menu, pattern="^client_menu$"))
application.add_handler(CallbackQueryHandler(client_handlers.show_schedule, pattern="^client_schedule$"))
application.add_handler(CallbackQueryHandler(client_handlers.show_day_trainings, pattern="^client_day_"))
application.add_handler(CallbackQueryHandler(client_handlers.show_register_menu, pattern="^client_register$"))
application.add_handler(CallbackQueryHandler(client_handlers.show_my_trainings, pattern="^client_cancel$"))
application.add_handler(CallbackQueryHandler(client_handlers.handle_register_for_training, pattern="^register_"))
application.add_handler(CallbackQueryHandler(client_handlers.cancel_registration, pattern="^cancel_reg_"))
application.add_handler(CallbackQueryHandler(client_handlers.show_training_details, pattern="^client_training_"))
application.add_handler(CallbackQueryHandler(client_handlers.show_profile, pattern="^test_profile$"))
application.add_handler(CallbackQueryHandler(client_handlers.start_change_name, pattern="^change_name$"))
application.add_handler(CommandHandler("change_name", client_handlers.handle_name_change))

# Додаємо логування для всіх обробників
print("DEBUG: All handlers registered:")
for handler in application.handlers[0]:
    if hasattr(handler, 'pattern'):
        print(f"DEBUG: Handler: {handler.callback.__name__} with pattern: {handler.pattern}")
    else:
        print(f"DEBUG: Handler: {handler.callback.__name__} (CommandHandler)")

# Запускаємо бота
if __name__ == "__main__":
    print("Starting bot...")
    asyncio.run(application.run_polling()) 