"""RQ worker entrypoint."""
from rq import Worker, Queue, Connection
import redis
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    redis_conn = redis.from_url(settings.REDIS_URL)
    
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work()

