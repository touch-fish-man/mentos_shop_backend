import threading
import time

from django.core.cache import cache

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes

class MemcacheLock:
    def __init__(self, lock_id, oid):
        self.lock_id = lock_id
        self.oid = oid
        self.condition = threading.Condition()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def acquire(self):
        timeout = time.monotonic() + LOCK_EXPIRE
        acquired = False
        while not acquired and time.monotonic() < timeout:
            acquired = cache.add(self.lock_id, self.oid, LOCK_EXPIRE)
            if not acquired:
                # wait for the lock to be released
                self.condition.acquire()
                self.condition.wait(timeout - time.monotonic())
                self.condition.release()
        if not acquired:
            raise Exception("Failed to acquire lock")

    def release(self):
        if cache.get(self.lock_id) == self.oid:
            cache.delete(self.lock_id)
            self.condition.acquire()
            self.condition.notify_all()
            self.condition.release()
