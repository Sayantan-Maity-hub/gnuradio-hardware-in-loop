import re
import time
from datetime import datetime
from ..remote_connections.cortexlab_remote import cortexlab_Remote
from .reservation_registry import (
    reservation_registry,
    update_reservation,
    get_reservation,
)


def parse_assigned_nodes(job_info):

    for field in ("assigned_hostnames", "assigned_network_address"):
        match = re.search(rf"(?im)^[ \t]*{field}[ \t]*=[ \t]*([^\r\n]*)", job_info)
        if not match:
            continue

        nodes = [
            f"node{number}"
            for number in re.findall(
                r"\bmnode(\d+)(?:\.cortexlab\.fr)?\b", match.group(1)
            )
        ]
        if nodes:
            return nodes

    return []


def reservation_monitor(job_id):
    print(f"reservation monitor started for {job_id}..")
    remote = None

    while True:
        try:
            reservation = get_reservation(job_id)

            if reservation is None:
                print(f"Reservation {job_id} removed.")
                break
            if remote is None:
                remote = cortexlab_Remote()

            stdout, stderr = remote.run(f"oarstat -fj {job_id}")

            job_info = stdout.read().decode()

            state_match = re.search(r"state\s*=\s*(\w+)", job_info)
            state = state_match.group(1) if state_match else "UNKNOWN"

            update_reservation(job_id, state=state)
            if state.lower() in ["terminated", "error", "finishing"]:

                break

            start_match = re.search(rf"scheduledStart\s*=\s*(.+)", job_info)
            submit_match = re.search(rf"submissionTime\s*=\s*(.+)", job_info)
            if start_match and submit_match:
                scheduled_start = start_match.group(1).strip()
                submit_time = submit_match.group(1).strip()

                update_reservation(job_id, scheduled_start=scheduled_start)

                start_dt = datetime.strptime(scheduled_start, "%Y-%m-%d %H:%M:%S")
                submit_dt = datetime.strptime(submit_time, "%Y-%m-%d %H:%M:%S")
                wait_min = max(0, int((start_dt - submit_dt).total_seconds() / 60))

                update_reservation(job_id, waiting_time=wait_min)

                nodes = parse_assigned_nodes(job_info)
                if nodes:
                    update_reservation(job_id, assigned_nodes=nodes)

        except Exception as e:

            if remote:
                try:
                    remote.close()
                except:
                    pass

            remote = None

        time.sleep(5)
    if remote:
        remote.close()
