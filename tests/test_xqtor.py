import unittest
from random import random

from xqtor import Xqtor
import time


class TestXqtor(unittest.TestCase):
    def test_passthrough_usage(self):
        def _task(x):
            time.sleep(x)
            return x

        executor = Xqtor(max_workers=1)
        t = time.time()
        results = list(executor.map(_task, [1, 1, 1, 1]))
        duration = time.time() - t
        self.assertEqual(results, [1, 1, 1, 1])
        self.assertLess(abs(duration - 4), 0.4)

    def test_basic_resource_usage(self):
        def _task(x):
            time.sleep(x)
            return x

        executor = Xqtor(available=2)
        t = time.time()
        results = list(executor.map((_task, 1), [1, 1, 1, 1]))
        duration = time.time() - t
        self.assertEqual(results, [1, 1, 1, 1])
        self.assertLess(abs(duration - 2), 0.2)

    def test_loadsa_tasks(self):
        def _task(x):
            time.sleep(x)
            return x

        # list of ((fn, resource), fn arg)
        submission_params = []
        for i in range(1000):
            # ((_task, resource_req), run_duration)
            submission_params.append(((_task, random()), random()))

        total_cpu_available = 25.0
        executor = Xqtor(available=total_cpu_available)
        t = time.time()
        futures = []
        for fn, arg in submission_params:
            futures.append(executor.submit(fn, arg))

        for f in futures:
            f.result()
        duration = time.time() - t

        total_cpu_seconds = sum([x[1] * x[0][1] for x in submission_params])
        expected_duration = total_cpu_seconds / total_cpu_available
        self.assertLess(abs(duration - expected_duration) / expected_duration, 0.1)


if __name__ == '__main__':
    unittest.main()
