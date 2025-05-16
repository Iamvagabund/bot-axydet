from sqlalchemy.orm import sessionmaker
from models import engine, User, Training, TrainingRegistration
from datetime import datetime, timedelta

def format_date(date):
    return date.strftime('%d.%m.%Y')

__all__ = [
    'get_or_create_user',
    'add_training',
    'get_trainings_by_date',
    'register_for_training',
    'cancel_registration',
    'get_user_registrations',
    'update_user_paid_trainings',
    'update_user_display_name',
    'get_all_users',
    'get_training_participants',
    'delete_training',
    'get_training_by_id',
    'get_user_by_id',
    'get_user_by_telegram_id',
    'get_user_training_registration',
    'delete_user_by_display_name',
    'reset_all_users_trainings',
    'update_user_expires_at',
    'create_training',
    'format_date'
]

Session = sessionmaker(bind=engine)

def get_or_create_user(telegram_id, display_name):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id, 
            display_name=display_name,
            paid_trainings=0,
            expires_at=None
        )
        session.add(user)
        session.commit()
    session.close()
    return user

def add_training(telegram_id: int, amount: int = 1) -> bool:
    """Добавляет тренировки пользователю"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return False
        if user.paid_trainings > 0:
            return False
        user.paid_trainings = amount
        now = datetime.utcnow()
        if now.month == 12:
            user.expires_at = datetime(now.year + 1, 1, now.day, 23, 59, 59)
        else:
            user.expires_at = datetime(now.year, now.month + 1, now.day, 23, 59, 59)
        session.commit()
        return True
    finally:
        session.close()

def get_trainings_by_date(date):
    session = Session()
    trainings = session.query(Training).filter(
        Training.date >= date,
        Training.date < date + timedelta(days=1)
    ).all()
    session.close()
    return trainings

def register_for_training(user_id, training_id):
    session = Session()
    try:
        # Отримуємо тренування
        training = session.query(Training).get(training_id)
        if not training:
            return None
            
        # Для персонального тренування не перевіряємо оплачені тренування
        if training.type != "Персональне тренування":
            # Перевіряємо чи є у користувача активні тренування
            user = session.query(User).get(user_id)
            if not user or user.paid_trainings <= 0:
                return None
                
            # Перевіряємо чи не істек абонемент
            if user.expires_at and user.expires_at < datetime.utcnow():
                user.paid_trainings = 0
                session.commit()
                return None
                
            # Зменшуємо кількість тренувань
            user.paid_trainings -= 1
            
        # Перевіряємо чи не записаний вже
        existing_reg = get_user_training_registration(user_id, training_id)
        if existing_reg:
            return None
            
        # Перевіряємо кількість учасників
        current_participants = get_training_participants(training_id)
        max_participants = 1 if training.type == "Персональне тренування" else 2
        if len(current_participants) >= max_participants:
            return None
            
        # Створюємо реєстрацію
        registration = TrainingRegistration(user_id=user_id, training_id=training_id)
        session.add(registration)
        session.commit()
        return registration
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def cancel_registration(registration_id):
    with Session() as session:
        try:
            registration = session.query(TrainingRegistration).get(registration_id)
            if registration:
                registration.is_cancelled = True
                # Повертаємо тренування тільки якщо це не персональне тренування
                training = session.query(Training).get(registration.training_id)
                if training and training.type != "Персональне тренування":
                    user = session.query(User).get(registration.user_id)
                    if user:
                        user.paid_trainings += 1
                session.commit()
                return registration
            return None
        except Exception as e:
            session.rollback()
            raise e

def get_user_registrations(user_id):
    with Session() as session:
        registrations = session.query(TrainingRegistration)\
            .filter(
                TrainingRegistration.user_id == user_id,
                TrainingRegistration.is_cancelled == False
            ).all()
        return registrations

def update_user_paid_trainings(user_id, package_type):
    """
    Добавляет тренировки пользователю в зависимости от типа пакета
    package_type: 1 - 8 тренировок, 2 - 4 тренировки, 3 - 1 тренировка
    """
    session = Session()
    user = session.query(User).get(user_id)
    if user:
        # Проверяем есть ли активные тренировки
        if user.paid_trainings > 0:
            return None  # Нельзя купить новый пакет пока есть активные тренировки
            
        # Устанавливаем количество тренировок и дату истечения
        if package_type == 1:
            user.paid_trainings = 8
        elif package_type == 2:
            user.paid_trainings = 4
        else:
            user.paid_trainings = 1
            
        # Устанавливаем дату истечения (конец дня через ровно месяц)
        now = datetime.utcnow()
        if now.month == 12:
            user.expires_at = datetime(now.year + 1, 1, now.day, 23, 59, 59)
        else:
            user.expires_at = datetime(now.year, now.month + 1, now.day, 23, 59, 59)
        session.commit()
    session.close()
    return user

def update_user_display_name(user_id, new_name):
    session = Session()
    user = session.query(User).get(user_id)
    if user:
        user.display_name = new_name
        session.commit()
    session.close()
    return user

def get_all_users():
    session = Session()
    users = session.query(User).all()
    session.close()
    return users

def get_training_participants(training_id):
    with Session() as session:
        training = session.query(Training).get(training_id)
        if not training:
            return []
        
        # Отримуємо всі активні реєстрації для цього тренування
        registrations = session.query(TrainingRegistration).filter(
            TrainingRegistration.training_id == training_id,
            TrainingRegistration.is_cancelled == False
        ).all()
        
        # Перевіряємо чи не перевищено ліміт учасників
        max_slots = 1 if training.type == "Персональне тренування" else 2
        if len(registrations) >= max_slots:
            return registrations[:max_slots]  # Повертаємо тільки перших max_slots учасників
        
        return registrations

def delete_training(training_id):
    session = Session()
    training = session.query(Training).get(training_id)
    if training:
        # Видаляємо всі реєстрації на це тренування
        session.query(TrainingRegistration).filter_by(training_id=training_id).delete()
        # Видаляємо тренування
        session.delete(training)
        session.commit()
    session.close()
    return training

def get_training_by_id(training_id):
    session = Session()
    training = session.query(Training).get(training_id)
    session.close()
    return training

def get_user_by_id(user_id):
    session = Session()
    user = session.query(User).get(user_id)
    session.close()
    return user

def get_user_by_telegram_id(telegram_id: int) -> User:
    print(f"DEBUG: get_user_by_telegram_id called with telegram_id={telegram_id}")
    return get_or_create_user(telegram_id, f"User {telegram_id}")

def get_user_training_registration(user_id, training_id):
    session = Session()
    try:
        registration = session.query(TrainingRegistration)\
            .filter(
                TrainingRegistration.user_id == user_id,
                TrainingRegistration.training_id == training_id,
                TrainingRegistration.is_cancelled == False
            ).first()
        return registration
    finally:
        session.close()

def delete_user_by_display_name(display_name):
    session = Session()
    try:
        # Знаходимо користувача за ім'ям
        user = session.query(User).filter(User.display_name == display_name).first()
        if user:
            # Видаляємо всі реєстрації користувача
            session.query(TrainingRegistration).filter_by(user_id=user.id).delete()
            # Видаляємо користувача
            session.delete(user)
            session.commit()
            print(f"DEBUG: User {display_name} deleted successfully")
            return True
        else:
            print(f"DEBUG: User {display_name} not found")
            return False
    except Exception as e:
        print(f"ERROR deleting user: {e}")
        session.rollback()
        return False
    finally:
        session.close() 

def reset_all_users_trainings():
    session = Session()
    try:
        # Обновляем всех пользователей
        users = session.query(User).all()
        for user in users:
            user.paid_trainings = 0
            user.expires_at = None
        session.commit()
        print(f"DEBUG: Reset trainings for {len(users)} users")
        return True
    except Exception as e:
        print(f"ERROR resetting trainings: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def update_user_expires_at(user_id: int, expires_at: datetime) -> None:
    """Оновлює дату закінчення тренувань користувача"""
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.expires_at = expires_at
            session.commit()
    finally:
        session.close()

def create_training(date, time, training_type):
    session = Session()
    training = Training(date=date, time=time, type=training_type)
    session.add(training)
    session.commit()
    session.refresh(training)
    session.close()
    return training 