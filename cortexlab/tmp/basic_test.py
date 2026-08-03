#!/usr/bin/env python3

import time

# STATE: PREPARING
time.sleep(15)

# STATE: READY

time.sleep(15)

# STATE: RUNNING
for i in range(15):
    print(f"Packet {i}")
    time.sleep(15)

# STATE: FINISHED
print("Done")
