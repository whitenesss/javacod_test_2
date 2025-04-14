import json
import redis


class RedisQueue:
    def __init__(self, queue_name='default_queue', **redis_kwargs):
        """
        Инициализация очереди Redis

        :param queue_name: имя очереди (ключ в Redis)
        :param redis_kwargs: параметры подключения к Redis (host, port, db и т.д.)
        """
        self.redis = redis.Redis(**redis_kwargs)
        self.queue_name = queue_name

    def publish(self, msg: dict):
        """
        Добавление сообщения в очередь

        :param msg: сообщение в виде словаря
        """
        # Сериализуем словарь в JSON строку
        serialized_msg = json.dumps(msg)
        # Добавляем в конец списка Redis
        self.redis.rpush(self.queue_name, serialized_msg)

    def consume(self) -> dict:
        """
        Получение сообщения из очереди (FIFO)

        :return: сообщение в виде словаря или None, если очередь пуста
        """
        # Блокирующее получение элемента из начала списка
        # (0 - бесконечное ожидание, можно указать timeout)
        _, serialized_msg = self.redis.blpop(self.queue_name)
        if serialized_msg:
            return json.loads(serialized_msg)
        return None

    def size(self) -> int:
        """
        Получение размера очереди

        :return: количество элементов в очереди
        """
        return self.redis.llen(self.queue_name)

    def is_empty(self) -> bool:
        """
        Проверка, пуста ли очередь

        :return: True если очередь пуста, иначе False
        """
        return self.size() == 0


if __name__ == '__main__':
    # Тестирование очереди
    q = RedisQueue(
        queue_name='test_queue',
        host='localhost',
        port=6379,
        db=0
    )

    # Очищаем очередь перед тестами (на случай предыдущих запусков)
    while not q.is_empty():
        q.consume()

    # Публикуем сообщения
    q.publish({'a': 1})
    q.publish({'b': 2})
    q.publish({'c': 3})

    # Проверяем порядок извлечения
    assert q.consume() == {'a': 1}
    assert q.consume() == {'b': 2}
    assert q.consume() == {'c': 3}
    print("Все тесты пройдены успешно!")