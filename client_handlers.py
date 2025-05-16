from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.ext.filters import Command
from datetime import datetime, timedelta
from database import (
    get_or_create_user, get_user_by_telegram_id, get_trainings_by_date,
    get_training_participants, get_user_training_registration, get_user_by_id,
    get_all_users, update_user_paid_trainings, update_user_expires_at, add_training,
    get_training_by_id, format_date, register_for_training
)
from config import ADMIN_IDS
from utils import format_date as utils_format_date
from sqlalchemy.orm import Session
from database import User, Session
import sqlalchemy
import sqlite3
import traceback

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

async def add_training_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды добавления тренировок"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды")
        return
        
    # Получаем ID пользователя из сообщения
    try:
        _, telegram_id, amount = update.message.text.split()
        telegram_id = int(telegram_id)
        amount = int(amount)
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Используйте: /add_training ID КОЛИЧЕСТВО")
        return
        
    # Проверяем существование пользователя
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        await update.message.reply_text("❌ Пользователь не найден")
        return
        
    # Добавляем тренировки
    if not add_training(telegram_id, amount):
        await update.message.reply_text(
            f"❌ Не удалось добавить тренировки. У пользователя уже есть действующий абонемент:\n"
            f"• Количество тренировок: {user.paid_trainings}\n"
            f"• Действует до: {user.expires_at.strftime('%d.%m.%Y') if user.expires_at else 'без срока действия'}\n\n"
            f"Сначала нужно использовать все тренировки из текущего абонемента."
        )
        return
        
    # Получаем обновленные данные пользователя
    user = get_user_by_telegram_id(telegram_id)
    await update.message.reply_text(
        f"✅ Добавлено {amount} тренировок пользователю {user.display_name}\n"
        f"📅 Действует до: {user.expires_at.strftime('%d.%m.%Y')}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        keyboard = [[InlineKeyboardButton("🚀 Почати", callback_data="client_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "👋 *Вітаємо в фітнес-студії АХУДЄТЬ!*\n\n"
            "🏋️‍♂️ *Наші переваги:*\n"
            "• Професійні тренери\n"
            "• Сучасне обладнання\n"
            "• Індивідуальний підхід\n"
            "• Зручний розклад\n\n"
            "🎯 *Для початку роботи натисніть кнопку 'Почати'*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_client_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаем пользователя только когда он нажимает "Почати" или если это админ
    user = get_or_create_user(
        update.effective_user.id,
        update.effective_user.full_name
    )
    
    keyboard = [
        [InlineKeyboardButton("📅 Розклад на тиждень", callback_data="client_schedule")],
        [InlineKeyboardButton("📝 Записатися на тренування", callback_data="client_register")],
        [InlineKeyboardButton("❌ Скасувати тренування", callback_data="client_cancel")],
        [InlineKeyboardButton("👤 Мій профіль", callback_data="test_profile")]
    ]
    
    # Если это админ, добавляем кнопку возврата в админ-панель
    if update.effective_user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔐 Повернутися до адмін-панелі", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"👋 *Вітаємо, {user.display_name}!*\n\n"
    
    # Показываем информацию о тренировках для всех пользователей
    if user.paid_trainings > 0:
        text += f"💰 *У вас оплачених тренувань у кількості - {user.paid_trainings}*\n"
        if user.expires_at:
            text += f"📅 *Дійсні до:* {user.expires_at.strftime('%d.%m.%Y')}\n\n"
        text += "Ви можете записатися на тренування через меню 'Записатися на тренування'\n\n"
    else:
        text += "❌ *У вас немає оплачених тренувань*\n\n"
        text += "Щоб оплатити тренування, ви можете:\n"
        text += "1️⃣ Натиснути 'Мій профіль' та обрати опцію оплати\n"
        text += "2️⃣ Якщо виникли складнощі, зверніться до адміністратора\n\n"
    
    text += "🎯 *Оберіть дію:*"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "😔 Тренування ще не додані.\n"
            "Спробуйте пізніше.",
            reply_markup=reply_markup
        )
        return
    
    # Формуємо текст розкладу
    text = "🏋️‍♂️ Розклад тренувань на тиждень:\n\n"
    
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
        
        text += f"📅 *{date.strftime('%d.%m.%Y')}*\n"
        text += f"*{weekday_ua}*\n"
        for training in sorted(trainings, key=lambda x: x.time):
            participants = get_training_participants(training.id)
            max_slots = 1 if training.type == "Персональне тренування" else 3
            is_registered = get_user_training_registration(user.id, training.id) is not None
            checkmark = "✅" if is_registered else ""
            text += f"  {training.time} - {training.type} ({len(participants)}/{max_slots}) {checkmark}\n"
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
    
    text = f"📝 *Оберіть час тренування:*\n\n"
    text += f"💰 *Залишок тренувань:* {user.paid_trainings}\n\n"
    text += f"📅 *{date.strftime('%d.%m.%Y')}*\n"
    text += f"*{weekday_ua}*\n\n"
    
    keyboard = []
    for training in sorted(trainings, key=lambda x: x.time):
        participants = get_training_participants(training.id)
        max_slots = 1 if training.type == "Персональне тренування" else 3
        is_registered = get_user_training_registration(user.id, training.id) is not None
        checkmark = "✅" if is_registered else ""
        text += f"⏰ *{training.time}* - {training.type} ({len(participants)}/{max_slots}) {checkmark}\n"
        
        # Додаємо кнопку часу
        keyboard.append([
            InlineKeyboardButton(
                f"⏰ {training.time} - {training.type}",
                callback_data=f"client_training_{training.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="client_register")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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
    
    text = f"💰 *Залишок тренувань:* {user.paid_trainings}\n\n"
    text += f"🏋️‍♂️ *Тренування*\n\n"
    text += f"📅 *{format_date(training.date)}*\n"
    text += f"*{weekday_ua}*\n"
    text += f"⏰ *{training.time}*\n"
    text += f"*{training.type}*\n"
    max_slots = 1 if training.type == "Персональне тренування" else 3
    text += f"👥 *Записано:* {len(participants)}/{max_slots}\n\n"
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
            "Тренування вже почалося або закінчилось.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="client_menu")]]),
            parse_mode='Markdown'
        )
        return
    
    # Перевіряємо чи є оплачені тренування тільки для групових тренувань
    if training.type != "Персональне тренування" and user.paid_trainings <= 0:
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
    
    # Перевіряємо чи є вільні місця
    participants = get_training_participants(training_id)
    max_slots = 1 if training.type == "Персональне тренування" else 3
    if len(participants) >= max_slots:
        await query.edit_message_text(
            "❌ *На жаль, всі місця на це тренування вже зайняті.*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"client_day_{training.date.strftime('%Y-%m-%d')}")]]),
            parse_mode='Markdown'
        )
        return
    
    # Викликаємо функцію з database.py
    registration = register_for_training(user.id, training_id)
    if registration:
        # Отримуємо оновлені дані
        user = get_user_by_telegram_id(telegram_id)  # Оновлюємо дані користувача
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
        if training.type != "Персональне тренування":
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
        user = get_user_by_telegram_id(update.effective_user.id)  # Оновлюємо дані користувача
        
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
            "❌ *У вас немає оплачених тренувань*\n\n"
            "Але ви можете записатися на індивідуальні заняття",
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
    
    # Формуємо текст меню
    text = f"📝 *Оберіть день для запису:*\n\n"
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
        
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {date.strftime('%d.%m.%Y')} ({weekday_ua})",
                callback_data=f"client_day_{date.strftime('%Y-%m-%d')}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="client_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = get_user_by_telegram_id(update.effective_user.id)

    text = f"👤 *Профіль*\n\n"
    text += f"*Ім'я:* {user.display_name}\n"
    
    if user.paid_trainings > 0:
        text += f"💰 *Залишок тренувань:* {user.paid_trainings}\n"
        if user.expires_at:
            text += f"📅 *Дійсні до:* {user.expires_at.strftime('%d.%m.%Y')}\n"
    else:
        text += "❌ *У вас немає активних тренувань*\n"
        if update.effective_user.id in ADMIN_IDS:
            text += "\n*Оберіть опцію оплати:*\n"
            text += "1️⃣ Абонемент на 8 тренувань\n"
            text += "2️⃣ Абонемент на 4 тренування\n"
            text += "3️⃣ Оплата одного тренування\n"
    
    keyboard = [
        [InlineKeyboardButton("✏️ Змінити ім'я", callback_data="change_name")]
    ]
    
    if update.effective_user.id in ADMIN_IDS and user.paid_trainings <= 0:
        keyboard.extend([
            [InlineKeyboardButton("💳 Абонемент на 8 тренувань", callback_data="buy_8_trainings")],
            [InlineKeyboardButton("💳 Абонемент на 4 тренування", callback_data="buy_4_trainings")],
            [InlineKeyboardButton("💳 Оплата одного тренування", callback_data="buy_1_training")]
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="client_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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

async def handle_buy_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = get_user_by_telegram_id(update.effective_user.id)
    if not user:
        return
    
    action = query.data
    # Устанавливаем время на конец дня через ровно месяц
    now = datetime.now()
    if now.month == 12:
        expires_at = datetime(now.year + 1, 1, now.day, 23, 59, 59)
    else:
        expires_at = datetime(now.year, now.month + 1, now.day, 23, 59, 59)
    
    if action == "buy_8_trainings":
        user.paid_trainings += 8
        user.expires_at = expires_at
        update_user_paid_trainings(user.id, 8)
        update_user_expires_at(user.id, expires_at)
        text = "✅ *Додано 8 тренувань до вашого балансу*\n"
        text += f"📅 *Дійсні до:* {expires_at.strftime('%d.%m.%Y')}"
    elif action == "buy_4_trainings":
        user.paid_trainings += 4
        user.expires_at = expires_at
        update_user_paid_trainings(user.id, 4)
        update_user_expires_at(user.id, expires_at)
        text = "✅ *Додано 4 тренування до вашого балансу*\n"
        text += f"📅 *Дійсні до:* {expires_at.strftime('%d.%m.%Y')}"
    elif action == "buy_1_training":
        user.paid_trainings += 1
        user.expires_at = expires_at
        update_user_paid_trainings(user.id, 1)
        update_user_expires_at(user.id, expires_at)
        text = "✅ *Додано 1 тренування до вашого балансу*\n"
        text += f"📅 *Дійсні до:* {expires_at.strftime('%d.%m.%Y')}"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад до профілю", callback_data="test_profile")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    users = get_all_users()
    text = "👥 *Керування користувачами*\n\n"
    text += "Оберіть користувача для керування:\n\n"
    
    keyboard = []
    for user in users:
        # Форматируем информацию о пользователе
        user_info = f"👤 {user.display_name}"
        if user.paid_trainings > 0:
            user_info += f" - {user.paid_trainings} тренувань"
            if user.expires_at:
                user_info += f" (до {user.expires_at.strftime('%d.%m.%Y')})"
        else:
            user_info += " - немає тренувань"
            
        keyboard.append([
            InlineKeyboardButton(
                user_info,
                callback_data=f"admin_user_{user.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split('_')[2])
    user = get_user_by_id(user_id)
    
    text = f"👤 *Керування користувачем:* {user.display_name}\n\n"
    text += f"💰 *Залишок тренувань:* {user.paid_trainings}\n\n"
    
    text += "*Оберіть дію:*\n"
    text += "1️⃣ Додати абонемент на 8 тренувань\n"
    text += "2️⃣ Додати абонемент на 4 тренування\n"
    text += "3️⃣ Додати одне тренування\n"
    text += "4️⃣ Додати персональне тренування\n"
    
    keyboard = [
        [InlineKeyboardButton("💳 Додати 8 тренувань", callback_data=f"admin_add_8_{user.id}")],
        [InlineKeyboardButton("💳 Додати 4 тренування", callback_data=f"admin_add_4_{user.id}")],
        [InlineKeyboardButton("💳 Додати 1 тренування", callback_data=f"admin_add_1_{user.id}")],
        [InlineKeyboardButton("💳 Додати персональне тренування", callback_data=f"admin_add_personal_{user.id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_add_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    _, _, action, user_id = query.data.split('_')
    user = get_user_by_id(int(user_id))
    
    if action == "8":
        amount = 8
    elif action == "4":
        amount = 4
    elif action == "personal":
        amount = 1  # Персональное тренировка тоже считается как 1 тренировка
    else:
        amount = 1
        
    # Добавляем тренировки через add_training
    if not add_training(user.telegram_id, amount):
        await query.edit_message_text(
            f"❌ Не удалось добавить тренировки. У пользователя уже есть действующий абонемент:\n"
            f"• Количество тренировок: {user.paid_trainings}\n"
            f"• Действует до: {user.expires_at.strftime('%d.%m.%Y') if user.expires_at else 'без срока действия'}\n\n"
            f"Сначала нужно использовать все тренировки из текущего абонемента.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="admin_users")]])
        )
        return
        
    # Получаем обновленные данные пользователя
    user = get_user_by_id(int(user_id))
    training_type = "персональное тренування" if action == "personal" else f"{amount} тренувань"
    await query.edit_message_text(
        f"✅ Добавлено {training_type} пользователю {user.display_name}\n"
        f"📅 Действует до: {user.expires_at.strftime('%d.%m.%Y')}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="admin_users")]])
    ) 