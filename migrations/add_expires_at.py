import sqlite3
from datetime import datetime

def migrate():
    # Подключаемся к базе данных
    conn = sqlite3.connect('fitness_studio.db')
    cursor = conn.cursor()
    
    try:
        # Добавляем колонку expires_at
        cursor.execute('ALTER TABLE users ADD COLUMN expires_at DATETIME')
        conn.commit()
        print("✅ Колонка expires_at успешно добавлена")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Колонка expires_at уже существует")
        else:
            print(f"❌ Ошибка при добавлении колонки: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate() 