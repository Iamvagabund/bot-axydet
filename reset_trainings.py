from database import reset_all_users_trainings

if __name__ == "__main__":
    if reset_all_users_trainings():
        print("✅ Всі тренування успішно скинуті")
    else:
        print("❌ Помилка при скиданні тренувань") 