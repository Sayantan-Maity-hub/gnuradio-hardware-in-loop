#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OFDM Analysis

Reads:
    parameters.json
    rx_payload.bin

Compares the received payload with the expected message
and generates result.json.

Exit codes:
    0 -> PASS
    1 -> FAIL
    2 -> ANALYSIS ERROR
"""

import json
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PARAMETER_FILE = os.path.join(
    SCRIPT_DIR,
    "parameters.json"
)

RESULT_FILE = os.path.join(
    SCRIPT_DIR,
    "result.json"
)


def write_result(status, reason, metrics=None):
    """
    Create result.json.
    """

    result = {
        "status": status,
        "reason": reason,
        "metrics": metrics or {}
    }

    try:
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)

        print(f"Result written to: {RESULT_FILE}")

    except Exception as e:
        print(
            f"ANALYSIS_ERROR: unable to write result.json: {e}"
        )


def main():

    # --------------------------------------------------
    # 1. Read parameters.json
    # --------------------------------------------------

    try:
        with open(PARAMETER_FILE, "r", encoding="utf-8") as f:
            params = json.load(f)

    except Exception as e:

        print(
            f"ANALYSIS_ERROR: unable to read parameters.json: {e}"
        )

        write_result(
            "failed",
            "Unable to read parameters.json",
            {
                "error": str(e)
            }
        )

        return 2

    # --------------------------------------------------
    # 2. Read expected message
    # --------------------------------------------------

    try:
        message = params["message"]

    except KeyError:

        print(
            "ANALYSIS_ERROR: 'message' not found in parameters.json"
        )

        write_result(
            "failed",
            "Missing 'message' in parameters.json",
            {}
        )

        return 2

    # --------------------------------------------------
    # 3. Convert expected message to bytes
    #
    # Example:
    #
    # "Hello CortexLab"
    #
    # becomes:
    #
    # b'Hello CortexLab'
    # --------------------------------------------------

    try:

        if not isinstance(message, str):
            raise ValueError(
                "'message' must be a string"
            )

        expected = message.encode("utf-8")

    except Exception as e:

        print(
            f"ANALYSIS_ERROR: invalid message '{message}': {e}"
        )

        write_result(
            "failed",
            "Invalid message",
            {
                "message": message,
                "error": str(e)
            }
        )

        return 2

    # --------------------------------------------------
    # 4. Find RX payload file
    # --------------------------------------------------

    rx_payload = params.get(
        "rx_payload",
        "rx_payload.bin"
    )

    output_file = os.path.join(
        SCRIPT_DIR,
        os.path.basename(rx_payload)
    )

    # --------------------------------------------------
    # 5. Check RX output
    # --------------------------------------------------

    if not os.path.exists(output_file):

        print(
            f"ANALYSIS_ERROR: RX output file not found: "
            f"{output_file}"
        )

        write_result(
            "failed",
            "RX output file not found",
            {
                "expected_message": message,
                "expected_bytes": expected.hex(),
                "rx_payload_file": output_file
            }
        )

        return 2

    # --------------------------------------------------
    # 6. Read received payload
    # --------------------------------------------------

    try:

        with open(output_file, "rb") as f:
            received = f.read()

    except Exception as e:

        print(
            f"ANALYSIS_ERROR: unable to read RX payload: {e}"
        )

        write_result(
            "failed",
            "Unable to read RX payload",
            {
                "rx_payload_file": output_file,
                "error": str(e)
            }
        )

        return 2

    # --------------------------------------------------
    # 7. Print diagnostics
    # --------------------------------------------------

    print(f"Expected bytes : {len(expected)}")
    print(f"Received bytes : {len(received)}")

    print(f"Expected       : {expected.hex()}")
    print(f"Received       : {received.hex()}")

    # --------------------------------------------------
    # 8. Compare
    # --------------------------------------------------

    message_match = received == expected

    metrics = {
        "expected_message": message,
        "expected_bytes": expected.hex(),
        "received_bytes": received.hex(),
        "expected_length": len(expected),
        "received_length": len(received),
        "message_match": message_match,
        "rx_payload_file": output_file
    }

    # --------------------------------------------------
    # 9. PASS
    # --------------------------------------------------

    if message_match:

        reason = (
            "Received payload exactly matches "
            "the transmitted message"
        )

        print("::STATUS:PASS:")
        print("OFDM RX analysis PASSED")
        print(f"Reason: {reason}")

        write_result(
            "passed",
            reason,
            metrics
        )

        return 0

    # --------------------------------------------------
    # 10. FAIL
    # --------------------------------------------------

    reason = (
        "Received payload does not match "
        "the transmitted message"
    )

    print("::STATUS:FAIL:")
    print("OFDM RX analysis FAILED")
    print(f"Reason: {reason}")

    if len(expected) != len(received):

        print(
            f"Length mismatch: expected {len(expected)}, "
            f"received {len(received)}"
        )

        metrics["length_mismatch"] = True

    else:

        metrics["length_mismatch"] = False

    write_result(
        "failed",
        reason,
        metrics
    )

    return 1


if __name__ == "__main__":
    sys.exit(main())