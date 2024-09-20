# Xcutor - a collection of Python `concurrent.futures.Executor` implementations

## ResourcePoolExecutor

A generic take on `ThreadPoolExecutor`.

For background, `ThreadPoolExecutor` schedules tasks based on:

* An integer number of workers
* Each submitted task uses exactly one worker.

`ResourcePoolExecutor` schedules tasks based on general resources. A resource pool is defined, and each task states
resources quantity it requires. The executor schedules tasks based on the availability of resources.

## Quick start

### Install

    pip install xcutor

### TL;DR

* set `available` to indicate total available resources, when constructing `ResourcePoolExecutor`
* `submit` tasks with a tuple of `(resource_quantity, task)`.
* The rest works the same as regular `ThreadPoolExecutor`.
* Constructor parameters are passed to an underlying `ThreadPoolExecutor` (except `available`).
  I.e. You can still set `max_workers` or `initializer` if needed.


### Example: using a float to represent CPU cores

```python

from xcutor import ResourcePoolExecutor
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


executor = ResourcePoolExecutor(available=5.5)

futures = []
futures.append(executor.submit((4.0, task_4_cpu)))
futures.append(executor.submit((2.0, task_2_cpu)))
futures.append(executor.submit((0.5, task_half_cpu)))

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
from xcutor import ResourcePoolExecutor


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


executor = ResourcePoolExecutor(available=CPUAndMemory(16, 64))
executor.submit((CPUAndMemory(4, 16), lambda: print("running task")))
executor.submit((CPUAndMemory(0, 16), lambda: print("running task")))
executor.submit((CPUAndMemory(8, 0), lambda: print("running task")))
executor.submit((CPUAndMemory(4, 32), lambda: print("running task")))
# The 4 tasks above will run immediately
executor.submit((CPUAndMemory(4, 16), lambda: print("running task")))
# This one will run when one of the first 4 tasks finishes
```
