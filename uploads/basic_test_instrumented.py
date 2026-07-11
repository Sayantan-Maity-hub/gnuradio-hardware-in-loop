import time

# STATE: PREPARING
print("__STATE__: PREPARING", flush=True)
time.sleep(15)

# STATE: READY
print("__STATE__: READY", flush=True)

time.sleep(15)

# STATE: RUNNING
print("__STATE__: RUNNING", flush=True)
for i in range(15):
    print(f"Packet {i}")
    time.sleep(15)

# STATE: FINISHED
print("__STATE__: FINISHED", flush=True)
print("Done")