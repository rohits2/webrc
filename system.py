


from concurrent.futures import ThreadPoolExecutor
from time import sleep, time
from typing import Callable
from threading import Lock, Thread
from loguru import logger

DAEMON_QUEUE = []
DAEMON_QUEUE_LOCK = Lock()

DAEMONS = set()

POOL = ThreadPoolExecutor()

def daemonize(interval: float=30, critical: bool=True, max_failures: int=9):
    def _daemonize_decorator(fn: Callable[..., None]) -> Callable[..., None]:
        def _daemonize_impl(*args, **kwargs):
            global DAEMONS
            nonlocal fn, interval, critical, max_failures
            n_failures = 0
            if f"{fn.__name__}/{id(fn)}" in DAEMONS:
                return
            DAEMONS |= f"{fn.__name__}/{id(fn)}"
            while (n_failures < max_failures and critical) or (not critical):
                start_time = time()
                try:
                    POOL.submit(fn, *args, **kwargs).result()
                    n_failures = 0
                except Exception as e:
                    logger.exception(f"Daemon {fn.__name__}/{id(fn)} crashed!")
                    n_failures += 1
                duration = time() - start_time
                if duration > interval:
                    n_failures += 1
                    logger.error(f"Daemon {fn.__name__}/{id(fn)} ran in {duration}s, but had deadline {interval}")
                else:
                    sleep(interval-duration)
        return _daemonize_impl
    return _daemonize_decorator
    