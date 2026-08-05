#!/usr/bin/env python3

import os
import sys
import subprocess

print("=" * 60)
print("DEBUG ENVIRONMENT")
print("=" * 60)

print(f"Hostname          : {os.uname().nodename}")
print(f"Current User      : {os.getenv('USER')}")
print(f"Current Directory : {os.getcwd()}")

print("\nPython Executable:")
print(sys.executable)

print("\nPython Version:")
print(sys.version)

print("\nPATH:")
print(os.environ.get("PATH"))

print("\nPYTHONPATH:")
print(os.environ.get("PYTHONPATH"))

print("\nsys.path:")
for p in sys.path:
    print(" ", p)

print("\nChecking GNU Radio...")

try:
    import gnuradio
    print("[OK] GNU Radio imported successfully.")
    print("Location:", gnuradio.__file__)
except Exception as e:
    print("[FAILED] Cannot import GNU Radio.")
    print(type(e).__name__, e)

print("\nChecking UHD...")

try:
    result = subprocess.run(
        ["uhd_find_devices"],
        capture_output=True,
        text=True
    )
    print("Return code:", result.returncode)
    print(result.stdout)
    print(result.stderr)
except Exception as e:
    print("Failed to execute uhd_find_devices:", e)

print("=" * 60)
print("END DEBUG")
print("=" * 60)