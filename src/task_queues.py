import sqlite3
import threading
import time
from contextlib import contextmanager

# Глобальная переменная для имени файла БД
DB_FILE = "task_queue.db"


# Инициализация БД
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                locked INTEGER DEFAULT 0
            )
        """)
        cursor.execute("DELETE FROM task_queue")  # Очищаем таблицу
        cursor.executemany(
            "INSERT INTO task_queue (task_name) VALUES (?)",
            [('Task 1',), ('Task 2',), ('Task 3',)]
        )
        conn.commit()


# Контекстный менеджер для подключений
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 5000")  # Таймаут для блокировок
    try:
        yield conn
    finally:
        conn.close()


# Потокобезопасное получение задачи
def fetch_task(conn):
    try:
        cursor = conn.cursor()
        # Блокируем первую доступную задачу
        cursor.execute("""
            UPDATE task_queue 
            SET locked = 1 
            WHERE id = (
                SELECT id 
                FROM task_queue 
                WHERE status = 'pending' AND locked = 0 
                ORDER BY id 
                LIMIT 1
            )
            RETURNING id, task_name
        """)

        task = cursor.fetchone()
        if task:
            conn.commit()
            return {'id': task[0], 'name': task[1]}

        return None

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в потоке {threading.current_thread().name}: {str(e)}")
        return None


# Рабочая функция потока
def worker(worker_id):
    print(f"[Поток {worker_id}] Запущен")
    with get_db_connection() as conn:
        task = fetch_task(conn)

        if task:
            print(f"[Поток {worker_id}] Взял задачу: {task['name']}")
            try:
                # Имитация обработки
                time.sleep(2)

                # Помечаем как выполненную
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE task_queue 
                    SET status = 'done', locked = 0 
                    WHERE id = ?
                """, (task['id'],))
                conn.commit()
                print(f"[Поток {worker_id}] Завершил задачу {task['name']}")
            except Exception as e:
                print(f"[Поток {worker_id}] Ошибка: {str(e)}")
                conn.rollback()
        else:
            print(f"[Поток {worker_id}] Нет доступных задач")


if __name__ == "__main__":
    # Инициализация БД
    init_db()

    # Запускаем потоки
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(0.1)  # Небольшая задержка между запусками

    # Ожидаем завершения
    for t in threads:
        t.join()

    # Проверяем результат
    print("\nИтоговое состояние:")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM task_queue ORDER BY id")
        for row in cursor.fetchall():
            print(row)