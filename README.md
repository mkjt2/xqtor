## Xqtor - a more flexible [`concurrent.futures.ThreadPoolExecutor`](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor)

The original `ThreadPoolExecutor` schedules tasks based on:

* An integer number of workers.
* Each submitted task uses exactly one worker.

`Xqtor` schedules tasks based on general resources units.

* Define quantity of total resource available.
* Each submitted task specifies resource quantity it requires.

## Quick start

### Install

    pip install xqtor

### TL;DR

* set `available` to indicate total available resources, when constructing `Xqtor`
* `submit` tasks with a tuple of `(resource_quantity, task)`.
* The rest works the same as regular `ThreadPoolExecutor`.
* Constructor parameters are passed to an underlying `ThreadPoolExecutor` (except `available`).
  I.e. You can still set `max_workers` or `initializer` if needed.

### Example: using a float to represent CPU cores

```python

from xqtor import Xqtor
import time


def task_4_cpu():
  print("running task_4_cpu")
  time.sleep(1)


def task_2_cpu():
  print("running task_2_cpu")
  time.sleep(1)


def task_half_cpu():
  print("running task_half_cpu")
  time.sleep(1)


executor = Xqtor(available=5.5)

futures = []
futures.append(executor.submit((task_4_cpu, 4.0)))
futures.append(executor.submit((task_2_cpu, 2.0)))
futures.append(executor.submit((task_half_cpu, 0.5)))

for future in futures:
  future.result()
```

Output:

```
# T=0
running task_4_cpu
running task_half_cpu

# T=1
running task_2_cpu
```

### What can I use to represent resources?

For simple cases use a number (float or int). E.g. Each task declares the need for X CPU cores? Or Y GB of RAM?

For more complex cases, define a custom resource. Resource values should support `+` / `-` and `>=`:

### Example: CPU + memory compound resource

```python
from xqtor import Xqtor


class CPUAndMemory:
    def __init__(self, cpu, memory):
        self.cpu = cpu
        self.memory = memory

    def __add__(self, other):
        return CPUAndMemory(self.cpu + other.cpu, self.memory + other.memory)

    def __sub__(self, other):
        return CPUAndMemory(self.cpu - other.cpu, self.memory - other.memory)

    def __ge__(self, other):
        return self.cpu >= other.cpu and self.memory >= other.memory


executor = Xqtor(available=CPUAndMemory(16, 64))
executor.submit((lambda: print("running task"), CPUAndMemory(4, 16)))
executor.submit((lambda: print("running task"), CPUAndMemory(0, 16)))
executor.submit((lambda: print("running task"), CPUAndMemory(8, 0)))
executor.submit((lambda: print("running task"), CPUAndMemory(4, 32)))
# The 4 tasks above will run immediately
executor.submit((lambda: print("running task"), CPUAndMemory(4, 16)))
# This one will run when one of the first 4 tasks finishes
```

## Contributions

Contributions are welcome!  Some possible areas (not exhaustive):

* Add support for `ProcessPoolExecutor` (currently only `ThreadPoolExecutor` is supported)
* Benchmarks (which may suggest perf improvement tasks)
* Test coverage
* Pluggable scheduling strategies
* General bugs
* General code quality improvements

## License

MIT