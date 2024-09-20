from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Condition


class ResourcePoolExecutor:
    def __init__(self, *args, **kwargs):
        self._available = kwargs.pop("available", None)
        self._executor = ThreadPoolExecutor(*args, **kwargs)
        self._queue = []
        self._lock = Lock()
        self._shutting_down = False

    def _schedule_more(self):
        # schedule another one
        schedulable = []
        for x, y, z in self._queue:
            if x is None or x <= self._available:
                self._available -= x
                schedulable.append((x, y, z))

        for tr in schedulable:
            self._queue.remove(tr)

        for x, y, z in schedulable:
            with z:
                z.notify()

    def submit(self, fn, *args, **kwargs):
        if isinstance(fn, tuple):
            fn, need_resource = fn
        else:
            need_resource = None

        cv = Condition()
        self._queue.append((need_resource, fn, cv))

        if need_resource is not None:
            assert self._available is not None

        def _fn(*args, **kwargs):
            try:
                with cv:
                    cv.wait()
                if self._shutting_down:
                    # Should we raise instead?
                    return
                return fn(*args, **kwargs)
            finally:
                with self._lock:
                    self._available += need_resource
                    self._schedule_more()

        try:
            return self._executor.submit(_fn, *args, **kwargs)
        finally:
            with self._lock:
                # schedule another one
                self._schedule_more()

    def map(self, *args, **kwargs):
        return self._executor.map(*args, **kwargs)

    def shutdown(self, *args, **kwargs):
        self._shutting_down = True
        return self._executor.shutdown(*args, **kwargs)
