import time
import sys

# Simple countdown
for i in range(10, 0, -1):
    print(f"\rWaiting {i} seconds...", end="", flush=True)
    time.sleep(1)
print("\rReady!              ")
