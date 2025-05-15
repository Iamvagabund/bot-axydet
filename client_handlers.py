from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from database import *
from config import ADMIN_IDS
from utils import format_date
from sqlalchemy.orm import Session
from database import User, Session
import sqlite3
import traceback

__all__ = [
    'start',
    'show_client_menu',
    'show_week_schedule',
    'show_day_trainings',
    'show_training_details',
    'handle_register_for_training',
    'cancel_registration',
    'show_my_trainings',
    'show_register_menu',
    'show_profile',
    'start_change_name',
    'handle_name_change'
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(
        update.effective_user.id,
        update.effective_user.full_name
    )
    
    if update.effective_user.id in ADMIN_IDS:
        keyboard = [
            [InlineKeyboardButton("🔐 Адмін-панель", callback_data="admin_menu")],
            [InlineKeyboardButton("👤 Меню клієнта", callback_data="client_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Вітаємо в боті фітнес-студії АХУДЄТЬ! Ви маєте доступ до адмін-панелі.",
            reply_markup=reply_markup
        )
    else:
        await show_client_menu(update, context)

async def show_client_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_by_telegram_id(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton("📅 Розклад на тиждень", callback_data="client_schedule")],
        [InlineKeyboardButton("📝 Записатися на тренування", callback_data="client_register")],
        [InlineKeyboardButton("❌ Скасувати тренування", callback_data="client_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"👋 *Вітаємо, {user.display_name}!*\n\n"
    text += f"💰 *Залишок тренувань:* {user.paid_trainings}\n\n"
    text += "🎯 *Оберіть дію:*"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_week_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    user = get_user_by_telegram_id(update.effective_user.id)
    
    # Збираємо всі тренування на два тижні
    trainings_by_day = {}
    for i in range(14):  # 7 днів поточного тижня + 7 днів наступного
        date = monday + timedelta(days=i)
        trainings = get_trainings_by_date(date)
        if trainings:  # Додаємо тільки якщо є тренування
            trainings_by_day[date] = trainings
    
    # Якщо немає тренувань, показуємо повідомлення
    if not trainings_by_day:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "😔 *На жаль, тренування ще не додані.*\n"
            "Спробуйте пізніше.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Формуємо текст розкладу
    text = "🏋️‍♂️ *Розклад тренувань на тиждень:*\n\n"
    
    for date, trainings in sorted(trainings_by_day.items()):
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
        
        text += f"📅 *{format_date(date)}*\n"
        text += f"*{weekday_ua}*\n"
        for training in sorted(trainings, key=lambda x: x.time):
            participants = get_training_participants(training.id)
            # Перевіряємо чи користувач вже записаний
            is_registered = any(reg.user_id == user.id for reg in participants)
            checkmark = "✅ " if is_registered else ""
            text += f"  {checkmark}{training.time} - {training.type} ({len(participants)} записів)\n"
        text += "\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_day_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    date_str = query.data.split('_')[2]
    date = datetime.strptime(date_str, '%Y-%m-%d')
    trainings = get_trainings_by_date(date)
    user = get_user_by_telegram_id(update.effective_user.id)
    
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
    
    text = f"📅 Тренування на {format_date(date)} ({weekday_ua}):\n\n"
    
    for training in sorted(trainings, key=lambda x: x.time):
        participants = get_training_participants(training.id)
        is_registered = any(reg.user_id == user.id for reg in participants)
        checkmark = "✅ " if is_registered else ""
        text += f"⏰ {checkmark}{training.time} - {training.type}\n"
        text += f"👥 Зареєстровано: {len(participants)} осіб\n\n"
    
    keyboard = []
    for training in trainings:
        keyboard.append([InlineKeyboardButton(
            f"✏️ {training.time} - {training.type}",
            callback_data=f"client_training_{training.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="client_schedule")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def show_training_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Отримуємо training_id з різних форматів callback_data
    if query.data.startswith('client_training_'):
        training_id = int(query.data.split('_')[2])
    else:  # для register_ та cancel_reg_
        training_id = int(query.data.split('_')[1])
    
    training = get_training_by_id(training_id)
    participants = get_training_participants(training_id)
    user = get_user_by_telegram_id(update.effective_user.id)
    
    weekday = training.date.strftime('%A')
    weekday_ua = {
        'Monday': 'Понеділок',
        'Tuesday': 'Вівторок',
        'Wednesday': 'Середа',
        'Thursday': 'Четвер',
        'Friday': "П'ятниця",
        'Saturday': 'Субота',
        'Sunday': 'Неділя'
    }[weekday]
    
    text = f"💰 Оплачені тренування: {user.paid_trainings}\n\n"
    text += f"🏋️‍♂️ *Тренування*\n\n"
    text += f"📅 *{format_date(training.date)}*\n"
    text += f"*{weekday_ua}*\n"
    text += f"⏰ *{training.time}*\n"
    text += f"*{training.type}*\n\n"
    text += f"👥 *Список учасників:*\n"
    
    if participants:
        for reg in participants:
            participant = get_user_by_id(reg.user_id)
            is_current_user = reg.user_id == user.id
            checkmark = "✅" if is_current_user else ""
            text += f"• {participant.display_name} {checkmark}\n"
    else:
        text += "• Поки що немає записів\n"
    
    keyboard = []
    # Перевіряємо чи користувач вже записаний
    is_registered = get_user_training_registration(user.id, training_id) is not None
    
    if is_registered:
        keyboard.append([InlineKeyboardButton("❌ Скасувати запис", callback_data=f"cancel_reg_{training_id}")])
    else:
        keyboard.append([InlineKeyboardButton("✅ Записатися", callback_data=f"register_{training_id}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Оновити", callback_data=f"client_training_{training_id}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"client_day_{training.date.strftime('%Y-%m-%d')}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_register_for_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    training_id = int(query.data.split('_')[1])
    telegram_id = update.effective_user.id
    user = get_user_by_telegram_id(telegram_id)
    
    # Перевіряємо чи тренування ще не почалося
    training = get_training_by_id(training_id)
    training_time = datetime.combine(training.date, datetime.strptime(training.time, '%H:%M').time())
    current_time = datetime.now()
    
    if training_time <= current_time:
        await query.edit_message_text(
            "❌ *На жаль, запис на це тренування вже закрито.*\n"
            "Тренування вже почалося.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]),
            parse_mode='Markdown'
        )
        return
    
    if user.paid_trainings <= 0:
        await query.edit_message_text(
            "❌ *У вас немає оплачених тренувань.*\n"
            "Зверніться до [@yurivynnyk](https://t.me/yurivynnyk) для поповнення.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]),
            parse_mode='Markdown'
        )
        return
    
    # Перевіряємо чи користувач вже записаний
    existing_reg = get_user_training_registration(user.id, training_id)
    if existing_reg:
        await query.edit_message_text(
            "❌ *Ви вже записані на це тренування.*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"client_training_{training_id}")]]),
            parse_mode='Markdown'
        )
        return
    
    # Викликаємо функцію з database.py
    registration = register_for_training(telegram_id, training_id)
    if registration:
        user.paid_trainings -= 1
        update_user_paid_trainings(user.id, -1)
        
        # Отримуємо оновлені дані
        training = get_training_by_id(training_id)
        participants = get_training_participants(training_id)
        
        weekday = training.date.strftime('%A')
        weekday_ua = {
            'Monday': 'Понеділок',
            'Tuesday': 'Вівторок',
            'Wednesday': 'Середа',
            'Thursday': 'Четвер',
            'Friday': "П'ятниця",
            'Saturday': 'Субота',
            'Sunday': 'Неділя'
        }[weekday]
        
        text = f"✅ *Ви успішно записалися на тренування!*\n\n"
        text += f"💰 *Залишок тренувань:* {user.paid_trainings}\n\n"
        text += f"🏋️‍♂️ *Тренування*\n\n"
        text += f"📅 *{format_date(training.date)}*\n"
        text += f"*{weekday_ua}*\n"
        text += f"⏰ *{training.time}*\n"
        text += f"*{training.type}*\n\n"
        text += f"👥 *Список учасників:*\n"
        
        if participants:
            for reg in participants:
                participant = get_user_by_id(reg.user_id)
                is_current_user = reg.user_id == user.id
                checkmark = "✅" if is_current_user else ""
                text += f"• {participant.display_name} {checkmark}\n"
        else:
            text += "• Поки що немає записів\n"
        
        keyboard = [
            [InlineKeyboardButton("❌ Скасувати запис", callback_data=f"cancel_reg_{training_id}")],
            [InlineKeyboardButton("🔄 Оновити", callback_data=f"client_training_{training_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data=f"client_day_{training.date.strftime('%Y-%m-%d')}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await query.edit_message_text(
            "❌ *Помилка при реєстрації.* Спробуйте ще раз.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]),
            parse_mode='Markdown'
        )

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Отримуємо training_id з різних форматів callback_data
    if query.data.startswith('cancel_reg_'):
        training_id = int(query.data.split('_')[2])
    else:  # для client_training_
        training_id = int(query.data.split('_')[2])
    
    user = get_user_by_telegram_id(update.effective_user.id)
    
    # Перевіряємо чи не занадто пізно скасовувати
    training = get_training_by_id(training_id)
    training_time = datetime.combine(training.date, datetime.strptime(training.time, '%H:%M').time())
    current_time = datetime.now()
    time_diff = training_time - current_time
    
    if time_diff.total_seconds() < 10800:  # 3 години = 10800 секунд
        await query.edit_message_text(
            "❌ *На жаль, скасувати запис вже неможливо.*\n"
            "Можна скасувати запис не пізніше ніж за 3 години до початку тренування.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]),
            parse_mode='Markdown'
        )
        return
    
    registration = get_user_training_registration(user.id, training_id)
    if registration:
        # Викликаємо функцію з database.py
        from database import cancel_registration as db_cancel_registration
        db_cancel_registration(registration.id)
        user.paid_trainings += 1
        update_user_paid_trainings(user.id, 1)
        
        # Отримуємо оновлені дані
        training = get_training_by_id(training_id)
        participants = get_training_participants(training_id)
        
        weekday = training.date.strftime('%A')
        weekday_ua = {
            'Monday': 'Понеділок',
            'Tuesday': 'Вівторок',
            'Wednesday': 'Середа',
            'Thursday': 'Четвер',
            'Friday': "П'ятниця",
            'Saturday': 'Субота',
            'Sunday': 'Неділя'
        }[weekday]
        
        text = f"✅ *Ви успішно скасували запис на тренування!*\n\n"
        text += f"💰 *Залишок тренувань:* {user.paid_trainings}\n\n"
        text += f"🏋️‍♂️ *Тренування*\n\n"
        text += f"📅 *{format_date(training.date)}*\n"
        text += f"*{weekday_ua}*\n"
        text += f"⏰ *{training.time}*\n"
        text += f"*{training.type}*\n\n"
        text += f"👥 *Список учасників:*\n"
        
        if participants:
            for reg in participants:
                participant = get_user_by_id(reg.user_id)
                is_current_user = reg.user_id == user.id
                checkmark = "✅" if is_current_user else ""
                text += f"• {participant.display_name} {checkmark}\n"
        else:
            text += "• Поки що немає записів\n"
        
        keyboard = [
            [InlineKeyboardButton("✅ Записатися", callback_data=f"register_{training_id}")],
            [InlineKeyboardButton("🔄 Оновити", callback_data=f"client_training_{training_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data=f"client_day_{training.date.strftime('%Y-%m-%d')}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await query.edit_message_text(
            "❌ *Помилка при скасуванні запису.*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]),
            parse_mode='Markdown'
        )

async def show_my_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = get_user_by_telegram_id(update.effective_user.id)
    registrations = get_user_registrations(user.id)
    
    if not registrations:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "😔 *У вас немає активних записів на тренування.*\n"
            "Запишіться на тренування в розкладі!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    text = "📋 *Ваші активні записи на тренування:*\n\n"
    keyboard = []
    
    # Сортуємо тренування за датою та часом
    sorted_registrations = sorted(
        registrations,
        key=lambda reg: (get_training_by_id(reg.training_id).date, get_training_by_id(reg.training_id).time)
    )
    
    for reg in sorted_registrations:
        training = get_training_by_id(reg.training_id)
        weekday = training.date.strftime('%A')
        weekday_ua = {
            'Monday': 'Понеділок',
            'Tuesday': 'Вівторок',
            'Wednesday': 'Середа',
            'Thursday': 'Четвер',
            'Friday': "П'ятниця",
            'Saturday': 'Субота',
            'Sunday': 'Неділя'
        }[weekday]
        
        text += f"📅 *{format_date(training.date)}*\n"
        text += f"*{weekday_ua}*\n"
        text += f"⏰ *{training.time}*\n"
        text += f"*{training.type}*\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"❌ Скасувати {format_date(training.date)} {training.time} - {training.type}",
                callback_data=f"cancel_reg_{training.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="client_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_register_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = get_user_by_telegram_id(update.effective_user.id)
    
    if user.paid_trainings <= 0:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ *У вас немає оплачених тренувань.*\n"
            "Зверніться до [@yurivynnyk](https://t.me/yurivynnyk) для поповнення.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    
    # Збираємо всі тренування на два тижні
    trainings_by_day = {}
    for i in range(14):  # 7 днів поточного тижня + 7 днів наступного
        date = monday + timedelta(days=i)
        trainings = get_trainings_by_date(date)
        if trainings:  # Додаємо тільки якщо є тренування
            trainings_by_day[date] = trainings
    
    # Якщо немає тренувань, показуємо повідомлення
    if not trainings_by_day:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "😔 *На жаль, тренування ще не додані.*\n"
            "Спробуйте пізніше.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Формуємо текст розкладу
    text = f"📝 *Оберіть тренування для запису:*\n\n"
    text += f"💰 *Залишок тренувань:* {user.paid_trainings}\n\n"
    keyboard = []
    
    for date, trainings in sorted(trainings_by_day.items()):
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
        
        text += f"📅 *{format_date(date)}*\n"
        text += f"*{weekday_ua}*\n"
        for training in sorted(trainings, key=lambda x: x.time):
            participants = get_training_participants(training.id)
            is_registered = any(reg.user_id == user.id for reg in participants)
            checkmark = "✅ " if is_registered else ""
            text += f"  {checkmark}{training.time} - {training.type} ({len(participants)} записів)\n"
        text += "\n"
        
        # Додаємо кнопку для перегляду тренувань цього дня
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {format_date(date)}",
                callback_data=f"client_day_{date.strftime('%Y-%m-%d')}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="client_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: ==========================================")
    print("DEBUG: show_profile called")
    print("DEBUG: update =", update)
    print("DEBUG: context =", context)
    print("DEBUG: ==========================================")
    try:
        query = update.callback_query
        print(f"DEBUG: callback_data = {query.data}")
        await query.answer()
        
        user = get_user_by_telegram_id(update.effective_user.id)
        print(f"DEBUG: User found: {user.display_name}")
        
        text = f"👤 *Особистий кабінет*\n\n"
        text += f"👋 *{user.display_name}*\n"
        text += f"💰 *Залишок тренувань:* {user.paid_trainings}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("✏️ Змінити ім'я", callback_data="change_name")],
            [InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]
        ]
        
        if update.effective_user.id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("🔐 Повернутися до адмін-панелі", callback_data="admin_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        print("DEBUG: Sending message")
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        print("DEBUG: Message sent")
    except Exception as e:
        print(f"ERROR in show_profile: {str(e)}")
        raise e

async def start_change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Implementation of start_change_name function
    pass

async def handle_name_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("DEBUG: ==========================================")
    print("DEBUG: handle_name_change called")
    print("DEBUG: update =", update)
    print("DEBUG: context =", context)
    print("DEBUG: context.user_data =", context.user_data)
    print("DEBUG: waiting_for_name =", context.user_data.get('waiting_for_name'))
    print("DEBUG: ==========================================")
    
    try:
        if not context.user_data.get('waiting_for_name'):
            print("DEBUG: Not waiting for name, ignoring message")
            return
            
        user_id = update.effective_user.id
        new_name = update.message.text.strip()
        print(f"DEBUG: New name = {new_name}")
        
        # Валідація імені
        if len(new_name) < 2:
            print("DEBUG: Name too short")
            await update.message.reply_text("❌ Ім'я повинно містити мінімум 2 символи")
            return
            
        if len(new_name) > 50:
            print("DEBUG: Name too long")
            await update.message.reply_text("❌ Ім'я не може бути довшим за 50 символів")
            return
            
        # Перевірка на допустимі символи (тільки літери, пробіли та дефіси)
        if not all(c.isalpha() or c.isspace() or c == '-' for c in new_name):
            print("DEBUG: Name contains invalid characters")
            await update.message.reply_text("❌ Ім'я може містити тільки літери, пробіли та дефіси")
            return
            
        # Перевірка на кількість слів
        words = new_name.split()
        if len(words) > 3:
            print("DEBUG: Too many words")
            await update.message.reply_text("❌ Ім'я не може містити більше 3 слів")
            return
            
        # Перевірка на довжину кожного слова
        if any(len(word) > 20 for word in words):
            print("DEBUG: Word too long")
            await update.message.reply_text("❌ Кожне слово не може бути довшим за 20 символів")
            return

        print("DEBUG: Name validation passed")
        print("DEBUG: Updating name in database")

        # Оновлюємо ім'я в базі даних
        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.display_name = new_name
                session.commit()
                print("DEBUG: Name updated in database")
            else:
                print("DEBUG: User not found")
        finally:
            session.close()

        print("DEBUG: Removing waiting_for_name flag")

        # Видаляємо прапорець очікування імені
        del context.user_data['waiting_for_name']

        print("DEBUG: Sending success message")

        # Повертаємо користувача до профілю
        keyboard = [[InlineKeyboardButton("◀️ Назад до профілю", callback_data="client_profile")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Ім'я успішно змінено на:* {new_name}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        print("DEBUG: Success message sent")
        
    except Exception as e:
        print(f"ERROR in handle_name_change: {e}")
        print(f"ERROR traceback: {traceback.format_exc()}")
        await update.message.reply_text("❌ Помилка при зміні імені. Спробуйте ще раз.") 