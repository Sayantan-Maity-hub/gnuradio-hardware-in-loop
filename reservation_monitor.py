import re 
import time
import threading
from reservation_registry import (reservations, update_job)

class ReservationMonitor(threading.Thread):
    def __init__(self, remote):
        super().__init__(daemon=True)
        self.remote = remote

    def run(self):
        while True:
            for job_id in list(reservations.keys()):
                try:
                    job_info = self.remote.run(f"oarstat -fj {job_id}")
                    state_match = re.search(r"state\s*=\s*(\w+)", job_info)
                    reservation_match = re.search(r"reservation\s*=\s*(\w+)", job_info)
                    start_match = re.search(r"scheduledStart\s*=\s*(.+)", job_info)
                    host_match = re.search(r"assigned_hostnames\s*=\s*(.+)", job_info)

                    state = (state_match.group(1).strip() if state_match else "UNKNOWN")
                    reservation_state = (reservation_match.group(1).strip() if reservation_match else None)
                    scheduled_start = (start_match.group(1).strip() if start_match else None)
                    nodes = []
                    if host_match:
                        host_string = host_match.group(1).strip()
                        if host_string:
                            nodes = host_string.split("+")
                    
                    update_job(job_id, state= state, reservation_state=reservation_state, scheduled_start=scheduled_start, nodes=nodes, last_update=time.time())
                except Exception as e:
                    print(f"Monitoring error for job"
                          f"{job_id}: {e}")
            time.sleep(5)