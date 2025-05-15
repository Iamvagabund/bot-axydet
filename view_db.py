from database import Session, User

def view_users():
    session = Session()
    users = session.query(User).all()
    print("\nCurrent users in database:")
    print("ID | Telegram ID | Name | Paid Trainings | Expires At")
    print("-" * 70)
    for user in users:
        print(f"{user.id} | {user.telegram_id} | {user.display_name} | {user.paid_trainings} | {user.expires_at}")
    session.close()

def reset_trainings():
    session = Session()
    users = session.query(User).all()
    for user in users:
        user.paid_trainings = 0
        user.expires_at = None
    session.commit()
    print("\nReset all users' trainings to 0")
    session.close()

if __name__ == "__main__":
    print("1. View all users")
    print("2. Reset all trainings to 0")
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        view_users()
    elif choice == "2":
        reset_trainings()
        view_users()  # Show the result
    else:
        print("Invalid choice") 