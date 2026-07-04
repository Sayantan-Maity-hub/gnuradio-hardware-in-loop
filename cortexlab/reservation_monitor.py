import re
import time
from datetime import datetime
from cortexlab_remote import cortexlab_Remote
from reservation_registry import(reservation_registry, update_reservation, get_reservation)
from scenario_generator import update_task_status

def reservation_monitor(job_id):
    print(f"reservation monitor started for {job_id}..")
    try:
        remote = cortexlab_Remote()

        while True:
            reservation = get_reservation(job_id)

            if reservation is None:
                print(f"Reservation {job_id} removed.")
                break

            job_info = remote.run(f"oarstat -fj {job_id}")

            state_match = re.search(r"state\s*=\s*(\w+)", job_info)
            state = (state_match.group(1) if state_match else "UNKNOWN")
            update_reservation(job_id, state=state)
            if state.lower() in ["terminated", "error", "finishing"]:
                print(f"Reservation {job_id} is finished")
                break


            start_match = re.search(f"scheduledStart\s*=\s*(.+)", job_info)
            submit_match = re.search(f"submissionTime\s*=\s*(.+)", job_info)
            if start_match and submit_match:
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
                    
                    nodes = host_string.split("+")
                    clean_nodes = []
                    for n in nodes:
                        short = (n.split(".")[0].replace("mnode", "node"))
                        clean_nodes.append(short)
                    update_reservation(job_id, assigned_nodes=clean_nodes)

            time.sleep(5)
                
    except Exception as e:
                print(f"Resevation monitor error for {job_id}: {e}")

