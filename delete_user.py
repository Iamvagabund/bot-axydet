from sqlalchemy.orm import sessionmaker
from models import engine, User, TrainingRegistration

Session = sessionmaker(bind=engine)
session = Session()

try:
    # Знаходимо користувача
    user = session.query(User).filter(User.display_name == "Це тест аккаунт").first()
    
    if user:
        # Видаляємо всі реєстрації користувача
        session.query(TrainingRegistration).filter_by(user_id=user.id).delete()
        # Видаляємо користувача
        session.delete(user)
        session.commit()
        print(f"Користувача {user.display_name} успішно видалено")
    else:
        print("Користувача не знайдено")
except Exception as e:
    print(f"Помилка: {e}")
    session.rollback()
finally:
    session.close() 