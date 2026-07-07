from cortexlab_remote import cortexlab_Remote
from reservation_registry import (get_reservation, get_all_reservation, reservation_registry) 
import time
import threading
from node_registry import update_job, clear_job

lock = threading.Lock()

def update_task(job_id, task_id, **kwargs):

    with lock:
        reservation = reservation_registry.get(job_id)

        if reservation is None:
            return

        for task in reservation.get("tasks", []):

            if str(task["task_id"]).strip() == str(task_id).strip():

                task.update(kwargs)

                reservation["last_update"] = time.time()

                return True
        return False

def minus_task_monitor(job_id, task_id):
    print(f"Task monitor started for {task_id}")

    remote = None

    while True:
            try:
                reservation = get_reservation(job_id)

                if reservation is None:
                        break
                if remote is None:
                    remote = cortexlab_Remote()

                output = remote.run(f"minus task info {task_id}")

                if "state=RUNNING" in output:
                    state = "RUNNING"
                    update_task(job_id, task_id, state=state)

                    task = next(
                        (
                            t for t in reservation["tasks"]
                            if str(t["task_id"]).strip() == str(task_id).strip()
                        ), None
                    )

                    if task:
                        for node in reservation["assigned_nodes"]:
                            update_job(node=node, job_id = job_id, task_id=task_id, description=task["description"], folder=task.get("folder"), state=state)

                elif "state=FINISHED"  in output:
                    state = "FINISHED"
                    update_task(job_id, task_id, state=state)
                    reservation = get_reservation(job_id)
                    for node in reservation["assigned_nodes"]:
                        clear_job(node)

                elif "state=ERROR" in output:
                    state = "ERROR"
                    update_task(job_id, task_id, state=state)
                    reservation = get_reservation(job_id)
                    for node in reservation["assigned_nodes"]:
                        clear_job(node)

                elif "state=WAITING"in output:
                    state = "WAITING"
                    update_task(job_id, task_id, state=state)
                
                elif "state=ABORTED" in output:
                    state = "ABORTED"
                    update_task(job_id, task_id, state=state)
                    reservation = get_reservation(job_id)
                    for node in reservation["assigned_nodes"]:
                        clear_job(node)
        
                else:
                    state = "UNKNOWN"
                    update_task(job_id, task_id, state = state)
                print(task_id, state)

            except Exception as e:
                print(f"Task monitor errror for {task_id}:{e}")
                if remote:
                    try:
                        remote.close()
                    except:
                        pass
                remote = None
            time.sleep(5)
    if remote:
        remote.close()
    print(f"Task monitor stopped fro {task_id}")