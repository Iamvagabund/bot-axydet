from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
print("DEBUG: Importing admin_handlers...")
import admin_handlers
print("DEBUG: Importing client_handlers...")
import client_handlers
print("DEBUG: Importing logging...")
import logging

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

# Створюємо бота
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Додаємо обробник помилок
application.add_error_handler(error_handler)

# Адмін-меню
application.add_handler(CommandHandler("admin", admin_handlers.admin_menu))
application.add_handler(CallbackQueryHandler(admin_handlers.admin_menu, pattern="^admin_menu$"))
application.add_handler(CallbackQueryHandler(admin_handlers.show_schedule, pattern="^admin_schedule$"))
application.add_handler(CallbackQueryHandler(admin_handlers.add_training_menu, pattern="^admin_add_training$"))
application.add_handler(CallbackQueryHandler(admin_handlers.edit_training_menu, pattern="^admin_edit_training$"))
application.add_handler(CallbackQueryHandler(admin_handlers.show_users, pattern="^admin_users$"))

# Додавання тренування
application.add_handler(CallbackQueryHandler(admin_handlers.add_training_time, pattern="^add_training_"))
application.add_handler(CallbackQueryHandler(admin_handlers.add_training_type, pattern="^add_time_"))
application.add_handler(CallbackQueryHandler(admin_handlers.save_training, pattern="^add_type_"))

# Перегляд і редагування тренувань
application.add_handler(CallbackQueryHandler(admin_handlers.view_existing_training, pattern="^view_training_"))
application.add_handler(CallbackQueryHandler(admin_handlers.view_day_trainings, pattern="^view_trainings_"))
application.add_handler(CallbackQueryHandler(admin_handlers.edit_existing_training, pattern="^edit_existing_training_"))
application.add_handler(CallbackQueryHandler(admin_handlers.change_training_type, pattern="^change_type_"))

# Редагування тренувань
application.add_handler(CallbackQueryHandler(admin_handlers.edit_day_trainings, pattern="^edit_day_"))
application.add_handler(CallbackQueryHandler(admin_handlers.edit_training, pattern="^edit_training_"))
application.add_handler(CallbackQueryHandler(admin_handlers.delete_training, pattern="^delete_training_"))

# Client handlers
print("DEBUG: Registering client handlers...")
application.add_handler(CommandHandler("start", client_handlers.start))
print("DEBUG: Registered start handler")
application.add_handler(CallbackQueryHandler(client_handlers.show_client_menu, pattern="^client_menu$"))
print("DEBUG: Registered show_client_menu handler")
application.add_handler(CallbackQueryHandler(client_handlers.show_week_schedule, pattern="^client_schedule$"))
print("DEBUG: Registered show_week_schedule handler")
application.add_handler(CallbackQueryHandler(client_handlers.show_register_menu, pattern="^client_register$"))
print("DEBUG: Registered show_register_menu handler")
application.add_handler(CallbackQueryHandler(client_handlers.show_my_trainings, pattern="^client_cancel$"))
print("DEBUG: Registered show_my_trainings handler")
application.add_handler(CallbackQueryHandler(client_handlers.handle_register_for_training, pattern="^register_"))
print("DEBUG: Registered handle_register_for_training handler")
application.add_handler(CallbackQueryHandler(client_handlers.cancel_registration, pattern="^cancel_reg_"))
print("DEBUG: Registered cancel_registration handler")
print("DEBUG: Registering show_profile handler with pattern='^test_profile$'")
application.add_handler(CallbackQueryHandler(client_handlers.show_profile, pattern="^test_profile$"))
print("DEBUG: Registered show_profile handler")
application.add_handler(CallbackQueryHandler(client_handlers.start_change_name, pattern="^change_name$"))
print("DEBUG: Registered start_change_name handler")
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, client_handlers.handle_name_change))
print("DEBUG: Registered handle_name_change handler")

# Додаємо логування для всіх обробників
print("DEBUG: All handlers registered:")
for handler in application.handlers[0]:
    if hasattr(handler, 'pattern'):
        print(f"DEBUG: Handler: {handler.callback.__name__} with pattern: {handler.pattern}")
    else:
        print(f"DEBUG: Handler: {handler.callback.__name__} (CommandHandler)")

# Запускаємо бота
if __name__ == '__main__':
    logger.info("Starting bot...")
    application.run_polling() 