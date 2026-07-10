import time

# STATE: PREPARING
print("Initializing USRP...")
time.sleep(15)

# STATE: READY
print("Receiver is ready")
time.sleep(15)

# STATE: RUNNING
for i in range(15):
    print(f"Packet {i}")
    time.sleep(15)

# STATE: FINISHED
print("Done")