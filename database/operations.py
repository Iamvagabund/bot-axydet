from sqlalchemy.orm import sessionmaker
from .models import engine, User, Training, TrainingRegistration
from datetime import datetime, timedelta
from typing import Optional

Session = sessionmaker(bind=engine)

def get_or_create_user(telegram_id: int, display_name: str) -> User:
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, display_name=display_name)
        session.add(user)
        session.commit()
    session.close()
    return user

def add_training(date: datetime, time: str, type: str) -> Training:
    session = Session()
    try:
        # Перетворюємо час у формат datetime
        hour, minute = map(int, time.split(':'))
        training_date = datetime(date.year, date.month, date.day, hour, minute)
        
        # Створюємо нове тренування
        training = Training(date=training_date, time=time, type=type)
        session.add(training)
        session.commit()
        return training
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_trainings_by_date(date: datetime) -> list[Training]:
    session = Session()
    # Отримуємо тренування тільки для конкретного дня
    start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
    end_date = datetime(date.year, date.month, date.day, 23, 59, 59)
    
    # Отримуємо всі тренування для цього дня
    trainings = session.query(Training).filter(
        Training.date >= start_date,
        Training.date <= end_date
    ).order_by(Training.time).all()
    
    session.close()
    return trainings

def register_for_training(telegram_id: int, training_id: int) -> Optional[TrainingRegistration]:
    """Реєстрація користувача на тренування"""
    with Session() as session:
        # Отримуємо користувача за telegram_id
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            return None
            
        # Перевіряємо чи користувач вже записаний
        existing_reg = session.query(TrainingRegistration).filter(
            TrainingRegistration.user_id == user.id,
            TrainingRegistration.training_id == training_id,
            TrainingRegistration.is_cancelled == False
        ).first()
        
        if existing_reg:
            return None
            
        # Створюємо новий запис
        registration = TrainingRegistration(
            user_id=user.id,
            training_id=training_id,
            registered_at=datetime.now(),
            is_cancelled=False
        )
        
        session.add(registration)
        session.commit()
        return registration

def cancel_registration(registration_id: int) -> Optional[TrainingRegistration]:
    session = Session()
    registration = session.query(TrainingRegistration).get(registration_id)
    if registration:
        registration.is_cancelled = True
        session.commit()
    session.close()
    return registration

def get_user_registrations(user_id: int) -> list[TrainingRegistration]:
    session = Session()
    registrations = session.query(TrainingRegistration).filter_by(
        user_id=user_id,
        is_cancelled=False
    ).all()
    session.close()
    return registrations

def update_user_paid_trainings(user_id: int, amount: int) -> Optional[User]:
    session = Session()
    user = session.query(User).get(user_id)
    if user:
        user.paid_trainings += amount
        session.commit()
    session.close()
    return user

def update_user_display_name(user_id: int, new_name: str) -> Optional[User]:
    session = Session()
    user = session.query(User).get(user_id)
    if user:
        user.display_name = new_name
        session.commit()
    session.close()
    return user

def get_all_users() -> list[User]:
    session = Session()
    users = session.query(User).all()
    session.close()
    return users

def get_training_participants(training_id: int) -> list[TrainingRegistration]:
    session = Session()
    registrations = session.query(TrainingRegistration).filter_by(
        training_id=training_id,
        is_cancelled=False
    ).all()
    session.close()
    return registrations

def delete_training(training_id: int) -> Optional[Training]:
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

def get_training_by_id(training_id: int) -> Optional[Training]:
    session = Session()
    training = session.query(Training).get(training_id)
    session.close()
    return training

def get_user_by_id(user_id: int) -> Optional[User]:
    session = Session()
    user = session.query(User).get(user_id)
    session.close()
    return user

def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user

def get_user_training_registration(user_id: int, training_id: int) -> Optional[TrainingRegistration]:
    session = Session()
    registration = session.query(TrainingRegistration).filter_by(
        user_id=user_id,
        training_id=training_id,
        is_cancelled=False
    ).first()
    session.close()
    return registration 