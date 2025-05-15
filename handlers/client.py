from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_or_create_user, get_trainings_by_date, get_training_by_id, get_training_participants
from utils import format_date, get_current_and_next_week_dates
from datetime import datetime

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_db = get_or_create_user(user.id, user.full_name)
    
    keyboard = [
        [InlineKeyboardButton("📅 Розклад тренувань", callback_data="schedule")],
        [InlineKeyboardButton("✅ Записатися на тренування", callback_data="register")],
        [InlineKeyboardButton("❌ Скасувати запис", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Вітаємо в боті фітнес-студії АХУДЄТЬ, {user.full_name}! Оберіть опцію:",
        reply_markup=reply_markup
    )

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Отримуємо дати поточного і наступного тижня
    dates = get_current_and_next_week_dates()
    keyboard = []
    user = get_user_by_telegram_id(update.effective_user.id)
    
    # Спочатку отримуємо всі тренування на два тижні
    all_trainings = []
    for date in dates:
        trainings = get_trainings_by_date(date)
        if trainings:
            all_trainings.extend(trainings)
    
    # Групуємо тренування по днях
    trainings_by_day = {}
    for training in all_trainings:
        day = training.date.strftime('%Y-%m-%d')
        if day not in trainings_by_day:
            trainings_by_day[day] = []
        trainings_by_day[day].append(training)
    
    # Показуємо тільки дні з тренуваннями
    for day, trainings in trainings_by_day.items():
        date = datetime.strptime(day, '%Y-%m-%d')
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
        
        # Додаємо кнопку з датою
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {format_date(date)} ({weekday_ua})",
                callback_data=f"day_{day}"
            )
        ])
    
    if not keyboard:
        await query.edit_message_text(
            "😔 На наступні два тижні немає запланованих тренувань.\n"
            "Спробуйте пізніше або зверніться до адміністратора."
        )
        return
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏋️‍♂️ Розклад тренувань на два тижні:\n"
        "Оберіть день для перегляду:",
        reply_markup=reply_markup
    )

async def show_day_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    date_str = query.data.split('_')[1]
    date = datetime.strptime(date_str, '%Y-%m-%d')
    trainings = get_trainings_by_date(date)
    
    keyboard = []
    for training in trainings:
        participants = get_training_participants(training.id)
        keyboard.append([
            InlineKeyboardButton(
                f"⏰ {training.time} - {training.type} ({len(participants)} учасників)",
                callback_data=f"training_{training.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад до розкладу", callback_data="schedule")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📅 Тренування на {format_date(date)}:\n"
        "Оберіть тренування для деталей:",
        reply_markup=reply_markup
    )

async def show_training_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    training_id = int(query.data.split('_')[1])
    training = get_training_by_id(training_id)
    participants = get_training_participants(training_id)
    
    participants_text = "\n".join([f"👤 {reg.user.display_name}" for reg in participants])
    if not participants_text:
        participants_text = "😔 Поки немає записаних учасників"
    
    keyboard = [
        [InlineKeyboardButton("✅ Записатися", callback_data=f"register_{training_id}")],
        [InlineKeyboardButton("◀️ Назад до розкладу", callback_data=f"day_{training.date.strftime('%Y-%m-%d')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🏋️‍♂️ Деталі тренування:\n\n"
        f"📅 Дата: {format_date(training.date)}\n"
        f"⏰ Час: {training.time}\n"
        f"🎯 Тип: {training.type}\n\n"
        f"👥 Учасники:\n{participants_text}",
        reply_markup=reply_markup
    ) 