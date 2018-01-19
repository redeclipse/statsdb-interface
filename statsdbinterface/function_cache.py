import time
from threading import Thread, Lock
import atexit
try:
    import config
    cache_enabled = config.CACHE
except (ImportError, AttributeError):
    cache_enabled = True

cache = {}
cache_cleaner_thread = None
cache_lock = Lock()
cache_cleaner_running = False


def cached(seconds, cattr=None):
    """
    Decorator, registers function to the cache.
    """
    if not cache_enabled:
        return lambda f: f

    def wrapper(f):
        def function(*args, **kwargs):
            # Construct key from the function id and arguments.
            if cattr is None:
                key = (id(f), args, tuple(kwargs.items()))
            else:
                # Used for class methods, change args[0] to an attribute.
                kargs = args[1:]
                key = (id(f), id(type(args[0])),
                       getattr(args[0], cattr), kargs,
                       tuple(kwargs.items()))
            needresults = False
            with cache_lock:
                if key not in cache:
                    needresults = True
            if needresults:
                results = f(*args, **kwargs)
                with cache_lock:
                    cache[key] = (time.time(), results, seconds)
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
    if not cache_enabled:
        return
    global cache_cleaner_running, cache_cleaner_thread
    if cache_cleaner_running:
        return
    cache_cleaner_thread = Thread(target=cleaner, daemon=True)
    cache_cleaner_running = True
    cache_cleaner_thread.start()
    atexit.register(cancel_cleaner)
