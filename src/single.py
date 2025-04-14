import time
import uuid
import datetime

from redis import Redis


def single(max_processing_time):
    def decorator(func):
        def wrapper(*args, **kwargs):
            redis = Redis(host="localhost", port=6379)
            lock_key = f"lock:{func.__module__}:{func.__name__}"
            lock_id = str(uuid.uuid4())
            locked = redis.set(lock_key, lock_id, nx=True, ex=int(max_processing_time.total_seconds()))
            if not locked:
                raise Exception(
                    "Функция уже выполняется на другом сервере!"
                )
            try:
                print(f"🔒 Блокировка установлена! ID: {lock_id}")
                return func(*args, **kwargs)
            finally:
                script = """
                                if redis.call("get", KEYS[1]) == ARGV[1] then
                                    return redis.call("del", KEYS[1])
                                else
                                    return 0
                                end
                                """
                redis.eval(script, 1, lock_key, lock_id)
                print("🔓 Блокировка снята!")
        return wrapper
    return decorator

@single(max_processing_time=datetime.timedelta(seconds=10))
def process_task():
    print("Начало выполнения задачи")
    time.sleep(5)
    print("Задача завершена")

if __name__ == "__main__":
    process_task()