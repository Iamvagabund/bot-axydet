from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from database import *
from config import TRAINING_TYPES, ADMIN_IDS, GROUP_CHAT_ID
from utils import format_date

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        if update.callback_query:
            await update.callback_query.answer("У вас немає доступу до адмін-панелі.")
        else:
            await update.message.reply_text("У вас немає доступу до адмін-панелі.")
        return

    keyboard = [
        [InlineKeyboardButton("📅 Розклад занять", callback_data="admin_schedule")],
        [InlineKeyboardButton("➕ Додати тренування", callback_data="admin_add_training")],
        [InlineKeyboardButton("✏️ Редагувати тренування", callback_data="admin_edit_training")],
        [InlineKeyboardButton("👥 Керування користувачами", callback_data="admin_users")],
        [InlineKeyboardButton("📋 Тренування завтра", callback_data="admin_tomorrow")],
        [InlineKeyboardButton("👤 Переглянути меню клієнта", callback_data="client_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text("Адмін-панель:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Адмін-панель:", reply_markup=reply_markup)

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Перевіряємо чи користувач адмін
    if update.effective_user.id not in ADMIN_IDS:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ У вас немає доступу до цієї функції.",
            reply_markup=reply_markup
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
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "😔 Тренування ще не додані.\n"
            "Додайте тренування через меню адміністратора.",
            reply_markup=reply_markup
        )
        return
    
    # Формуємо текст розкладу
    text = "🏋️‍♂️ Розклад тренувань на тиждень:\n\n"
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
            text += f"  {training.time} {training.type} ({len(participants)} записів)\n"
        text += "\n"
        
        # Додаємо кнопку для редагування тренувань цього дня
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ Редагувати {format_date(date)}",
                callback_data=f"edit_day_{date.strftime('%Y-%m-%d')}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_day_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    date_str = query.data.split('_')[2]
    date = datetime.strptime(date_str, '%Y-%m-%d')
    trainings = get_trainings_by_date(date)
    
    text = f"Розклад на {date.strftime('%d.%m.%Y')}:\n\n"
    for training in trainings:
        participants = get_training_participants(training.id)
        text += f"{training.time} - {training.type}\n"
        text += f"Зареєстровано: {len(participants)} осіб\n\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_schedule")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def add_training_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    today = datetime.now().date()
    # Знаходимо понеділок поточного тижня
    monday = today - timedelta(days=today.weekday())
    keyboard = []
    
    # Показуємо 14 днів (поточний тиждень + наступний)
    for i in range(14):
        date = monday + timedelta(days=i)
        weekday = date.strftime('%A')
        weekday_ua = {
            'Monday': 'Пн',
            'Tuesday': 'Вт',
            'Wednesday': 'Ср',
            'Thursday': 'Чт',
            'Friday': 'Пт',
            'Saturday': 'Сб',
            'Sunday': 'Нд'
        }[weekday]
        text = f"{date.strftime('%d.%m.%Y')} ({weekday_ua})"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"add_training_{date.strftime('%Y-%m-%d')}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Виберіть дату для додавання тренування:", reply_markup=reply_markup)

async def add_training_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    date_str = query.data.split('_')[2]
    context.user_data['training_date'] = date_str
    date = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Отримуємо існуючі тренування на цей день
    existing_trainings = get_trainings_by_date(date)
    existing_times = {t.time: t for t in existing_trainings}
    
    keyboard = []
    for hour in range(8, 22):
        time = f"{hour:02d}:00"
        if time in existing_times:
            training = existing_times[time]
            text = f"✅ {time} - {training.type}"
            callback_data = f"view_existing_{training.id}"
        else:
            text = f"⏰ {time}"
            callback_data = f"add_time_{time}"
        keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_add_training")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Виберіть час тренування:", reply_markup=reply_markup)

async def add_training_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    time = query.data.split('_')[2]
    date = datetime.strptime(context.user_data['training_date'], '%Y-%m-%d')
    
    # Перевіряємо чи не існує вже тренування на цей час
    existing_trainings = get_trainings_by_date(date)
    if any(t.time == time for t in existing_trainings):
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"add_training_{date.strftime('%Y-%m-%d')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"❌ На цей час ({time}) вже є тренування.\n"
            f"Будь ласка, виберіть інший час.",
            reply_markup=reply_markup
        )
        return
    
    context.user_data['training_time'] = time
    
    keyboard = []
    for type in TRAINING_TYPES:
        keyboard.append([InlineKeyboardButton(type, callback_data=f"add_type_{type}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"add_training_{date.strftime('%Y-%m-%d')}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Виберіть тип тренування:", reply_markup=reply_markup)

async def save_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    training_type = query.data.split('_')[2]
    date = datetime.strptime(context.user_data['training_date'], '%Y-%m-%d')
    time = context.user_data['training_time']
    
    training = add_training(date, time, training_type)
    
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
    
    keyboard = [
        [InlineKeyboardButton("➕ Додати ще тренування", callback_data="admin_add_training")],
        [InlineKeyboardButton("◀️ Назад до адмін-меню", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"✅ Тренування успішно додано!\n\n"
        f"📅 Дата: {format_date(date)} ({weekday_ua})\n"
        f"⏰ Час: {time}\n"
        f"🏋️‍♂️ Тип: {training_type}"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def edit_training_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    today = datetime.now().date()
    keyboard = []
    
    for i in range(7):
        date = today + timedelta(days=i)
        trainings = get_trainings_by_date(date)
        if trainings:
            text = f"{date.strftime('%d.%m.%Y')} - {len(trainings)} тренувань"
            keyboard.append([InlineKeyboardButton(text, callback_data=f"edit_day_{date.strftime('%Y-%m-%d')}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Виберіть день для редагування тренувань:", reply_markup=reply_markup)

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    users = get_all_users()
    keyboard = []
    
    for user in users:
        text = f"{user.display_name} - {user.paid_trainings} тренувань"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"user_{user.id}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Список користувачів:", reply_markup=reply_markup)

async def user_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split('_')[1])
    user = get_user_by_id(user_id)
    
    keyboard = [
        [InlineKeyboardButton("➕ Додати 1 тренування", callback_data=f"add_paid_1_{user_id}")],
        [InlineKeyboardButton("➕ Додати 2 тренування", callback_data=f"add_paid_2_{user_id}")],
        [InlineKeyboardButton("➕ Додати 3 тренування", callback_data=f"add_paid_3_{user_id}")],
        [InlineKeyboardButton("➕ Додати 5 тренувань", callback_data=f"add_paid_5_{user_id}")],
        [InlineKeyboardButton("➕ Додати 10 тренувань", callback_data=f"add_paid_10_{user_id}")],
        [InlineKeyboardButton("✏️ Змінити ім'я", callback_data=f"change_name_{user_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_users")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Користувач: {user.display_name}\nОплачені тренування: {user.paid_trainings}"
    await query.edit_message_text(text, reply_markup=reply_markup)

async def edit_day_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    date_str = query.data.split('_')[2]
    date = datetime.strptime(date_str, '%Y-%m-%d')
    trainings = get_trainings_by_date(date)
    
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
    
    keyboard = []
    for training in trainings:
        participants = get_training_participants(training.id)
        text = f"{format_date(date)} {training.time} - {training.type} ({len(participants)} осіб)"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"edit_training_{training.id}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_edit_training")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Виберіть тренування для редагування на {format_date(date)} ({weekday_ua}):", reply_markup=reply_markup)

async def edit_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    training_id = int(query.data.split('_')[2])
    training = get_training_by_id(training_id)
    
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
    
    keyboard = [
        [InlineKeyboardButton("✏️ Змінити тип тренування", callback_data=f"edit_existing_training_{training_id}")],
        [InlineKeyboardButton("❌ Видалити тренування", callback_data=f"delete_training_{training_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"edit_day_{training.date.strftime('%Y-%m-%d')}")]
    ]
    
    text = (
        f"📅 Тренування на {format_date(training.date)} ({weekday_ua}):\n\n"
        f"⏰ Час: {training.time}\n"
        f"🏋️‍♂️ Тип: {training.type}\n"
        f"👥 Зареєстровано: {len(get_training_participants(training_id))} осіб"
    )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def delete_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    training_id = int(query.data.split('_')[2])
    
    # Отримуємо тренування перед видаленням
    training = get_training_by_id(training_id)
    if not training:
        keyboard = [[InlineKeyboardButton("◀️ Назад до редагування", callback_data="admin_edit_training")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("❌ Тренування не знайдено", reply_markup=reply_markup)
        return
    
    # Зберігаємо інформацію про тренування перед видаленням
    training_info = f"{format_date(training.date)} {training.time} {training.type}"
    
    # Видаляємо тренування
    session = Session()
    try:
        session.delete(training)
        session.commit()
        keyboard = [[InlineKeyboardButton("◀️ Назад до редагування", callback_data="admin_edit_training")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"✅ Тренування успішно видалено!\n\n"
            f"📅 {training_info}",
            reply_markup=reply_markup
        )
    except Exception as e:
        session.rollback()
        keyboard = [[InlineKeyboardButton("◀️ Назад до редагування", callback_data="admin_edit_training")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("❌ Помилка при видаленні тренування", reply_markup=reply_markup)
    finally:
        session.close()

async def view_day_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    date_str = query.data.split('_')[2]
    date = datetime.strptime(date_str, '%Y-%m-%d')
    trainings = get_trainings_by_date(date)
    
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
    keyboard = []
    
    for training in trainings:
        participants = get_training_participants(training.id)
        text += f"⏰ {training.time} - {training.type}\n"
        text += f"👥 Зареєстровано: {len(participants)} осіб\n\n"
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ Редагувати {training.time}",
                callback_data=f"edit_existing_training_{training.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_add_training")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def edit_existing_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    training_id = int(query.data.split('_')[3])
    training = get_training_by_id(training_id)
    
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
    
    keyboard = []
    for type in TRAINING_TYPES:
        if type != training.type:  # Не показуємо поточний тип
            keyboard.append([InlineKeyboardButton(type, callback_data=f"change_type_{training_id}_{type}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"view_trainings_{training.date.strftime('%Y-%m-%d')}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"✏️ Редагування тренування:\n\n"
        f"📅 Дата: {format_date(training.date)} ({weekday_ua})\n"
        f"⏰ Час: {training.time}\n"
        f"🏋️‍♂️ Поточний тип: {training.type}\n\n"
        f"Виберіть новий тип тренування:"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def view_existing_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    training_id = int(query.data.split('_')[2])
    training = get_training_by_id(training_id)
    
    if not training:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"add_training_{training.date.strftime('%Y-%m-%d')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("❌ Тренування не знайдено", reply_markup=reply_markup)
        return
    
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
    
    keyboard = [
        [InlineKeyboardButton("✏️ Змінити тип тренування", callback_data=f"edit_existing_training_{training_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"add_training_{training.date.strftime('%Y-%m-%d')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"📅 Тренування на {format_date(training.date)} ({weekday_ua}):\n\n"
        f"⏰ Час: {training.time}\n"
        f"🏋️‍♂️ Тип: {training.type}\n"
        f"👥 Зареєстровано: {len(get_training_participants(training_id))} осіб"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def change_training_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    training_id = int(parts[2])
    new_type = parts[3]
    
    # Оновлюємо тип тренування
    training = get_training_by_id(training_id)
    if training:
        training.type = new_type
        session = Session()
        session.merge(training)
        session.commit()
        session.close()
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"view_trainings_{training.date.strftime('%Y-%m-%d')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"✅ Тип тренування змінено на: {new_type}",
            reply_markup=reply_markup
        )
    else:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_add_training")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Помилка при зміні типу тренування",
            reply_markup=reply_markup
        )

async def add_paid_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    amount = int(parts[2])
    user_id = int(parts[3])
    
    user = get_user_by_id(user_id)
    if user:
        user.paid_trainings += amount
        session = Session()
        session.merge(user)
        session.commit()
        session.close()
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"user_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"✅ Додано {amount} тренувань!\n\n"
            f"Користувач: {user.display_name}\n"
            f"Оплачені тренування: {user.paid_trainings}",
            reply_markup=reply_markup
        )
    else:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Користувача не знайдено",
            reply_markup=reply_markup
        )

async def change_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = int(query.data.split('_')[2])
    context.user_data['editing_user_id'] = user_id
    
    keyboard = [[InlineKeyboardButton("◀️ Скасувати", callback_data=f"user_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Введіть нове ім'я користувача:",
        reply_markup=reply_markup
    )

async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'editing_user_id' not in context.user_data:
        return
    
    user_id = context.user_data['editing_user_id']
    new_name = update.message.text
    
    user = get_user_by_id(user_id)
    if user:
        user.display_name = new_name
        session = Session()
        session.merge(user)
        session.commit()
        session.close()
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"user_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✅ Ім'я змінено на: {new_name}",
            reply_markup=reply_markup
        )
    else:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_users")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ Користувача не знайдено",
            reply_markup=reply_markup
        )
    
    del context.user_data['editing_user_id']

async def show_tomorrow_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    tomorrow = datetime.now().date() + timedelta(days=1)
    trainings = get_trainings_by_date(tomorrow)
    
    if not trainings:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "😔 *На завтра тренувань немає.*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    text = f"📅 *Тренування на завтра ({format_date(tomorrow)}):*\n\n"
    
    for training in sorted(trainings, key=lambda x: x.time):
        participants = get_training_participants(training.id)
        text += f"⏰ *{training.time} - {training.type}*\n"
        text += f"👥 *Зареєстровано:* {len(participants)} осіб\n"
        
        if participants:
            text += "*Список учасників:*\n"
            for reg in participants:
                user = get_user_by_id(reg.user_id)
                text += f"  • {user.display_name}\n"
        else:
            text += "*Поки що немає записів*\n"
        text += "\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown') 