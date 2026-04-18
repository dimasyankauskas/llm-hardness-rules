[TIMEOUT]

[FILE: counter.py]
```
import time

counter = 0

def increment_counter(amount: int) -> int:
    global counter
    current = counter
    time.sleep(0.001)   # simulates work
    counter = current + amount
    return counter

```