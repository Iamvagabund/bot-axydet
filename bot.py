import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler
from config import TELEGRAM_TOKEN, ADMIN_IDS
from admin_handlers import (
    admin_menu,
    show_admin_schedule,
    show_day_schedule,
    add_training_menu,
    edit_training_menu,
    show_users,
    show_tomorrow_trainings,
    user_management,
    add_paid_trainings,
    handle_add_package,
    change_name_start,
    change_name,
    add_training_time,
    add_training_type,
    save_training,
    view_existing_training,
    view_day_trainings,
    edit_existing_training,
    change_training_type,
    edit_day_trainings,
    edit_training,
    delete_training
)
from client_handlers import (
    start, show_client_menu, show_schedule, show_day_trainings,
    show_training_details, handle_register_for_training, cancel_registration,
    show_my_trainings, show_register_menu, show_profile,
    start_change_name, handle_name_change, handle_buy_trainings,
    show_admin_users_menu, show_admin_user_actions, handle_admin_add_trainings,
    add_training_handler
)
from telegram.ext import filters

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # Створюємо застосунок
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Додаємо обробники команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_training", add_training_handler))
    application.add_handler(CommandHandler("admin", admin_menu))

    # Додаємо обробники callback-запитів для адміна
    application.add_handler(CallbackQueryHandler(admin_menu, pattern="^admin_menu$"))
    application.add_handler(CallbackQueryHandler(show_admin_schedule, pattern="^admin_schedule$"))
    application.add_handler(CallbackQueryHandler(show_day_schedule, pattern="^admin_day_"))
    application.add_handler(CallbackQueryHandler(add_training_menu, pattern="^admin_add_training$"))
    application.add_handler(CallbackQueryHandler(add_training_time, pattern="^add_training_"))
    application.add_handler(CallbackQueryHandler(view_existing_training, pattern="^view_existing_"))
    application.add_handler(CallbackQueryHandler(add_training_type, pattern="^add_time_"))
    application.add_handler(CallbackQueryHandler(save_training, pattern="^add_type_"))
    application.add_handler(CallbackQueryHandler(edit_training_menu, pattern="^admin_edit_training$"))
    application.add_handler(CallbackQueryHandler(edit_day_trainings, pattern="^edit_day_"))
    application.add_handler(CallbackQueryHandler(edit_training, pattern="^edit_training_"))
    application.add_handler(CallbackQueryHandler(delete_training, pattern="^delete_training_"))
    application.add_handler(CallbackQueryHandler(view_day_trainings, pattern="^view_trainings_"))
    application.add_handler(CallbackQueryHandler(edit_existing_training, pattern="^edit_existing_training_"))
    application.add_handler(CallbackQueryHandler(change_training_type, pattern="^change_type_"))
    application.add_handler(CallbackQueryHandler(show_admin_users_menu, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(show_admin_user_actions, pattern="^admin_user_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_admin_add_trainings, pattern="^admin_add_[148]_\d+$"))
    application.add_handler(CallbackQueryHandler(change_name_start, pattern="^change_name_"))
    application.add_handler(CallbackQueryHandler(show_tomorrow_trainings, pattern="^admin_tomorrow$"))

    # Додаємо обробники callback-запитів для клієнтів
    application.add_handler(CallbackQueryHandler(show_client_menu, pattern="^client_menu$"))
    application.add_handler(CallbackQueryHandler(show_schedule, pattern="^client_schedule$"))
    application.add_handler(CallbackQueryHandler(show_day_trainings, pattern="^client_day_"))
    application.add_handler(CallbackQueryHandler(show_training_details, pattern="^client_training_"))
    application.add_handler(CallbackQueryHandler(handle_register_for_training, pattern="^register_"))
    application.add_handler(CallbackQueryHandler(cancel_registration, pattern="^cancel_reg_"))
    application.add_handler(CallbackQueryHandler(show_my_trainings, pattern="^client_my_trainings$"))
    application.add_handler(CallbackQueryHandler(show_register_menu, pattern="^client_register$"))
    application.add_handler(CallbackQueryHandler(show_my_trainings, pattern="^client_cancel$"))
    application.add_handler(CallbackQueryHandler(show_profile, pattern="^test_profile$"))
    application.add_handler(CallbackQueryHandler(start_change_name, pattern="^change_name$"))
    application.add_handler(CallbackQueryHandler(handle_buy_trainings, pattern="^buy_[148]_trainings?$"))
    
    # Додаємо обробники текстових повідомлень
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_change))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, change_name))

    # Запускаємо бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 