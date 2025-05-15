from database import Session, User

def reset_trainings(telegram_id):
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            print(f"До: ID: {user.id}, Name: {user.display_name}, Trainings: {user.paid_trainings}")
            user.paid_trainings = 0
            session.commit()
            print(f"После: ID: {user.id}, Name: {user.display_name}, Trainings: {user.paid_trainings}")
            print("✅ Тренировки успешно сброшены")
        else:
            print("❌ Пользователь не найден")
    finally:
        session.close()

if __name__ == "__main__":
    reset_trainings(396869465)  # ID пользователя с 8 тренировками 