import time
from threading import Thread, Lock
import atexit
cache = {}
cache_cleaner_thread = None
cache_lock = Lock()
cache_cleaner_running = False


def cached(seconds):
    """
    Decorator, registers function to the cache.
    """
    def wrapper(f):
        def function(*args, **kwargs):
            # Construct key from the function id and arguments.
            key = (id(f), args, tuple(kwargs.items()))
            with cache_lock:
                timeout = (time.time() - cache[key][0]) >= seconds
                if key not in cache or timeout:
                    cache[key] = (time.time(), f(*args, **kwargs), seconds)
                return cache[key][1]
        return function

    return wrapper


def cleaner():
    while cache_cleaner_running:
        # Clean every minute, but periodically test for exit.
        for i in range(0, 60 * 10):
            time.sleep(0.1)
            if not cache_cleaner_running:
                return
        todelete = []
        for key in cache:
            if time.time() - cache[key][0] >= cache[key][2]:
                todelete.append(key)
        for key in todelete:
            with cache_lock:
                cache.pop(key)


def cancel_cleaner():
    global cache_cleaner_running
    cache_cleaner_running = False


def setup():
    global cache_cleaner_running, cache_cleaner_thread
    if cache_cleaner_running:
        return
    cache_cleaner_thread = Thread(target=cleaner, daemon=True)
    cache_cleaner_running = True
    cache_cleaner_thread.start()
    atexit.register(cancel_cleaner)
