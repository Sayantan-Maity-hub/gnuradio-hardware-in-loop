#!/usr/bin/env python3

import json
import time

try:
    # STATE: PREPARING
    time.sleep(5)

    # STATE: READY

    time.sleep(5)

    # STATE: RUNNING
    packets_received = 0
    for i in range(5):
        print(f"Packet {i}", flush=True)
        packets_received += 1
        time.sleep(5)

    # STATE: FINISHED
    print("Done", flush=True)
    print(
        "::RESULT::"
        + json.dumps(
            {
                "status": "passed",
                "message": "Basic packet reception experiment completed successfully",
                "metrics": {
                    "packets_received": packets_received,
                },
            }
        ),
        flush=True,
    )
except Exception as error:
    print(
        "::RESULT::"
        + json.dumps(
            {
                "status": "failed",
                "message": str(error),
                "metrics": {},
            }
        ),
        flush=True,
    )
    raise
