import re
import time
from datetime import datetime
from cortexlab_remote import cortexlab_Remote
from reservation_registry import(reservation_registry, update_reservation)

def reservation_monitor():
    print("reservation monitor started..")
    remote = cortexlab_Remote()

    while True:
        for job_id in list(reservation_registry.keys()):
            try:
                job_info = remote.run(f"oarstat -fj {job_id}")

                state_match = re.search(r"state\s*=\s*(\w+)", job_info)
                state = (state_match.group(1) if state_match else "UNKNOWN")
                if state.lower() in ["terminated", "error", "finishing"]:
                    update_reservation(job_id, state = "Finished")

                update_reservation(job_id, state = state)

                start_match = re.search(f"scheduledStart\s*=\s*(.+)", job_info)
                submit_match = re.search(f"submissionTime\s*=\s*(.+)", job_info)
                if start_match:
                    scheduled_start = (start_match.group(1).strip())
                    submit_time = (submit_match.group(1).strip())

                    update_reservation(job_id, scheduled_start=scheduled_start)

                    start_dt = datetime.strptime(scheduled_start, "%Y-%m-%d %H:%M:%S")
                    submit_dt = datetime.strptime(submit_time, "%Y-%m-%d %H:%M:%S")
                    wait_min = max(0, int((start_dt - submit_dt).total_seconds()/60))
                    print(wait_min)

                    update_reservation(job_id, waiting_time=wait_min)
                    
                host_match = re.search(r"assigned_hostnames\s*=\s*(.+)", job_info)
                if host_match:
                    host_string = (host_match.group(1).strip())
                    if host_string:
                        nodes = host_string.split("+")
                        clean_nodes = []
                        for n in nodes:
                            short = (n.split(".")[0].replace("mnode", "node"))
                            clean_nodes.append(short)
                        update_reservation(job_id, assigned_nodes=clean_nodes)
                    
                
            except Exception as e:
                print(f"Resevation monitor error for {job_id}: {e}")
        time.sleep(5)
