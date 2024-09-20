from concurrent.futures import ThreadPoolExecutor, Executor
from threading import Lock, Condition


class Xqtor(Executor):
    def __init__(self, *args, **kwargs):
        self._available = kwargs.pop("available", None)
        if kwargs.get("max_workers") is None:
            kwargs["max_workers"] = 1024 ** 4
        self._executor = ThreadPoolExecutor(*args, **kwargs)

        # queue of tasks, based on resource asks
        self._q = []

        # protects access to _q and _available
        self._lock = Lock()
        self._shutting_down = False

    def _schedule_more(self):
        assert self._lock.locked()
        # schedule another one
        schedulable = []

        # need_resource, fn, cv, phase
        for x, y, z, p in self._q:
            if x is None or x <= self._available:
                if x is not None:
                    self._available -= x
                schedulable.append((x, y, z, p))
                p.append("GO")

        # remove schedulable stuff from the queue
        for tr in schedulable:
            self._q.remove(tr)

        # unleash the schedulable stuff
        for x, y, z, p in schedulable:
            with z:
                z.notify()

    def submit(self, fn, *args, **kwargs):
        """
        Submit a task to the executor.
        :param fn: a callable, or a tuple of (callable, resource_requirement)
        :param args:
        :param kwargs:
        :return:
        """
        if isinstance(fn, tuple):
            fn, resource_req = fn
        else:
            resource_req = None

        cv = Condition()

        # tasks wait for "OK" to show up in the phase list, before starting to run
        phase = []
        self._q.append((resource_req, fn, cv, phase))

        if resource_req is not None:
            assert self._available is not None

        def _fn(*args, **kwargs):
            try:
                with cv:
                    while not phase:
                        cv.wait()
                if self._shutting_down:
                    # Should we raise instead?
                    return
                return fn(*args, **kwargs)
            finally:
                with self._lock:
                    if resource_req is not None:
                        self._available += resource_req
                    self._schedule_more()

        try:
            return self._executor.submit(_fn, *args, **kwargs)
        finally:
            with self._lock:
                # schedule another one
                self._schedule_more()

    def shutdown(self, *args, **kwargs):
        self._shutting_down = True
        return self._executor.shutdown(*args, **kwargs)
