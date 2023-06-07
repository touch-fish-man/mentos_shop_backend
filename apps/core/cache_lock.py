import logging
import time

from django.core.cache import cache

LOCK_EXPIRE = 120 * 10  # Lock expires in 10 minutes

class memcache_lock:
    def __init__(self, lock_id, oid):
        self.lock_id = lock_id
        self.oid = oid

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
                time.sleep(0.5)
        return acquired

    def release(self):
        if cache.get(self.lock_id) == self.oid:
            cache.delete(self.lock_id)