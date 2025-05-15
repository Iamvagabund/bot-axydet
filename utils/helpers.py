from datetime import datetime, timedelta
from typing import List, Optional

def format_date(date: datetime) -> str:
    """Форматує дату у формат dd.mm.yyyy"""
    return date.strftime('%d.%m.%Y')

def get_week_dates(start_date: Optional[datetime] = None) -> List[datetime]:
    """Повертає список дат на тиждень вперед"""
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return [start_date + timedelta(days=i) for i in range(7)]

def get_two_weeks_dates(start_date: Optional[datetime] = None) -> List[datetime]:
    """Повертає список дат на два тижні вперед"""
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return [start_date + timedelta(days=i) for i in range(14)]

def get_current_week_dates() -> List[datetime]:
    """Повертає список дат поточного тижня (з понеділка по неділю)"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # Знаходимо понеділок поточного тижня
    monday = today - timedelta(days=today.weekday())
    # Повертаємо всі дні тижня
    return [monday + timedelta(days=i) for i in range(7)]

def get_current_and_next_week_dates() -> List[datetime]:
    """Повертає список дат поточного і наступного тижня (з понеділка по неділю)"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # Знаходимо понеділок поточного тижня
    monday = today - timedelta(days=today.weekday())
    # Повертаємо всі дні поточного і наступного тижня
    return [monday + timedelta(days=i) for i in range(14)] 