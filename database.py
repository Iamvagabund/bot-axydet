from sqlalchemy.orm import sessionmaker, joinedload
from models import engine, User, Training, TrainingRegistration
from datetime import datetime, timedelta

Session = sessionmaker(bind=engine)

def get_or_create_user(telegram_id, display_name):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, display_name=display_name)
        session.add(user)
        session.commit()
    session.close()
    return user

def add_training(date, time, type):
    session = Session()
    training = Training(date=date, time=time, type=type)
    session.add(training)
    session.commit()
    session.close()
    return training

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
        # Перевіряємо чи користувач вже записаний
        existing_reg = get_user_training_registration(user_id, training_id)
        if existing_reg:
            return None
            
        # Створюємо нову реєстрацію
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

def update_user_paid_trainings(user_id, amount):
    session = Session()
    user = session.query(User).get(user_id)
    if user:
        user.paid_trainings += amount
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
    session = Session()
    try:
        registrations = session.query(TrainingRegistration)\
            .filter(
                TrainingRegistration.training_id == training_id,
                TrainingRegistration.is_cancelled == False
            ).all()
        return registrations
    finally:
        session.close()

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
    print(f"DEBUG: get_user_by_telegram_id called with telegram_id={telegram_id}")  # Додаємо логування
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        print(f"DEBUG: User found: {user.display_name if user else 'None'}")  # Додаємо логування
        if not user:
            print("DEBUG: User not found, creating new user")  # Додаємо логування
            user = User(
                telegram_id=telegram_id,
                display_name=f"User {telegram_id}",
                paid_trainings=0
            )
            session.add(user)
            session.commit()
            print(f"DEBUG: New user created: {user.display_name}")  # Додаємо логування
        return user
    finally:
        session.close()
        print("DEBUG: Session closed")  # Додаємо логування

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