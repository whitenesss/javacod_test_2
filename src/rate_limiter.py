import time
import random

import redis


class RateLimitExceed(Exception):
    pass


class RateLimiter:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.window_size = 3  # окно в секундах
        self.max_requests = 5  # максимальное количество запросов

    def test(self) -> bool:
        """
        Проверяет, можно ли выполнить запрос.
        Возвращает True, если лимит не превышен, и False в противном случае.
        """
        current_time = time.time()
        window_start = current_time - self.window_size

        # Генерируем уникальный ключ для каждого пользователя/сервиса
        key = "rate_limit:api_requests"

        # Удаляем все записи старше текущего окна
        self.redis.zremrangebyscore(key, '-inf', window_start)

        # Получаем количество запросов в текущем окне
        request_count = self.redis.zcard(key)

        if request_count < self.max_requests:
            # Добавляем текущий запрос в отсортированное множество
            self.redis.zadd(key, {str(current_time): current_time})
            # Устанавливаем время жизни ключа на случай, если запросы прекратятся
            self.redis.expire(key, self.window_size)
            return True
        else:
            return False


def make_api_request(rate_limiter: RateLimiter):
    if not rate_limiter.test():
        raise RateLimitExceed
    else:
        # какая-то бизнес логика
        pass


if __name__ == '__main__':
    rate_limiter = RateLimiter()

    for _ in range(50):
        time.sleep(random.uniform(0.1, 0.5))

        try:
            make_api_request(rate_limiter)
        except RateLimitExceed:
            print("Rate limit exceed!")
        else:
            print("All good")