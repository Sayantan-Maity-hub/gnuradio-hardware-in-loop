from cortexlab_remote import cortexlab_Remote
from reservation_registry import get_all_reservation, get_reservation,reservation_registry
import time
import threading

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

    remote = cortexlab_Remote()
    try:
        while True:
            reservation = get_reservation(job_id)

            if reservation is None:
                    break
            output = remote.run(f"minus task info {task_id}")

            if "state=RUNNING" in output:
                state = "RUNNING"
                update_task(job_id, task_id, state=state)

            elif "state=FINISHED"  in output:
                state = "FINISHED"
                update_task(job_id, task_id, state=state)

            elif "state=ERROR" in output:
                state = "ERROR"
                update_task(job_id, task_id, state=state)

            elif "state=WAITING"in output:
                state = "WAITING"
                update_task(job_id, task_id, state=state)
    
            else:
                state = "UNKNOWN"
                update_task(job_id, task_id, state = state)
            print(task_id, state)

            if state.upper() in ["FINISHED", "ERROR", "ABORTED"]:
                update_task(job_id, task_id, state=state)
                break
        time.sleep(5)
    except Exception as e:
        print(f"Task monitor errror for {task_id}:{e}")

    finally:
        remote.close()
        print(f" Task monitor stopped for {task_id}")