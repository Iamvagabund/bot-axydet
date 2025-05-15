from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Отримуємо дати поточного і наступного тижня
    dates = get_current_and_next_week_dates()
    
    # Отримуємо всі тренування на два тижні
    all_trainings = []
    for date in dates:
        trainings = get_trainings_by_date(date)
        if trainings:  # Додаємо тільки якщо є тренування
            all_trainings.extend(trainings)
    
    # Якщо немає тренувань, показуємо повідомлення
    if not all_trainings:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "😔 Тренування ще не додані.\n"
            "Додайте тренування через меню адміністратора.",
            reply_markup=reply_markup
        )
        return
    
    # Якщо є тренування, створюємо клавіатуру
    keyboard = []
    for training in all_trainings:
        date = training.date
        weekday = date.strftime('%A')
        weekday_ua = {
            'Monday': 'Понеділок',
            'Tuesday': 'Вівторок',
            'Wednesday': 'Середа',
            'Thursday': 'Четвер',
            'Friday': "П'ятниця",
            'Saturday': 'Субота',
            'Sunday': 'Неділя'
        }[weekday]
        
        # Додаємо кнопку з датою і часом
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {format_date(date)} ({weekday_ua}) {training.time} - {training.type}",
                callback_data=f"admin_training_{training.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏋️‍♂️ Розклад тренувань на два тижні:",
        reply_markup=reply_markup
    )

async def show_day_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    date_str = query.data.split('_')[2]  # admin_day_YYYY-MM-DD
    date = datetime.strptime(date_str, '%Y-%m-%d')
    trainings = get_trainings_by_date(date)
    
    keyboard = []
    for training in trainings:
        participants = get_training_participants(training.id)
        keyboard.append([
            InlineKeyboardButton(
                f"⏰ {training.time} - {training.type} ({len(participants)} записів)",
                callback_data=f"admin_training_{training.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад до розкладу", callback_data="show_schedule")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    weekday = date.strftime('%A')
    weekday_ua = {
        'Monday': 'Понеділок',
        'Tuesday': 'Вівторок',
        'Wednesday': 'Середа',
        'Thursday': 'Четвер',
        'Friday': "П'ятниця",
        'Saturday': 'Субота',
        'Sunday': 'Неділя'
    }[weekday]
    
    await query.edit_message_text(
        f"📅 Тренування на {format_date(date)} ({weekday_ua}):\n"
        "Оберіть тренування для редагування:",
        reply_markup=reply_markup
    ) 