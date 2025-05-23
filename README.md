# Fitness Studio Bot

Telegram бот для управления тренировками в фитнес-студии.

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/bot-axydet.git
cd bot-axydet
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл конфигурации:
```bash
cp config.example.py config.py
```

4. Отредактируйте `config.py`:
- Замените `YOUR_BOT_TOKEN_HERE` на токен вашего бота
- Замените `YOUR_TELEGRAM_ID` на ваш Telegram ID
- Замените `YOUR_GROUP_CHAT_ID` на ID вашей группы

## Запуск

```bash
python main.py
```

## Разработка

- `config.py` добавлен в `.gitignore` и не будет отправляться в репозиторий
- Для локальной разработки используйте свой `config.py` с тестовыми данными
- Основной бот продолжит работать с оригинальным `config.py` на сервере

## Функціонал

### Для адміністратора:
- Перегляд розкладу занять
- Додавання нових тренувань
- Редагування існуючих тренувань
- Керування користувачами (додавання оплачених тренувань, зміна імені)

### Для клієнтів:
- Перегляд розкладу на тиждень
- Запис на тренування
- Скасування запису на тренування
- Перегляд своїх запланованих тренувань

## Структура проекту

- `bot.py` - головний файл бота
- `config.py` - налаштування та конфігурація
- `models.py` - моделі бази даних
- `database.py` - функції для роботи з базою даних
- `admin_handlers.py` - обробники для адміністратора
- `client_handlers.py` - обробники для клієнтів 