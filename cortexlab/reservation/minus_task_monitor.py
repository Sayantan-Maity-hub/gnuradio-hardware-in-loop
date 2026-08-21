import threading
import time

from ..remote_connections.cortexlab_remote import cortexlab_Remote

from ..nodes.node_registry import clear_job, update_job
from ..nodes.monitor_nodes import monitor_nodes
from .reservation_registry import (
    get_reservation,
    reservation_registry,
)

task_monitor_lock = threading.Lock()


node_monitor_lock = threading.Lock()

def update_task(job_id, task_id, **kwargs):

    with task_monitor_lock:
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

    remote = None
    node_monitor_thread = None
    while True:
        try:
            reservation = get_reservation(job_id)

            if reservation is None:
                break
            if remote is None:
                remote = cortexlab_Remote()

            stdout, stderr = remote.run(f"minus task info {task_id}")
            output = stdout.read().decode()
            print(output)
            
            if "state=RUNNING" in output:
                state = "RUNNING"
                update_task(job_id, task_id, state=state)

                # Node state monitor thread
                if node_monitor_thread is None or not node_monitor_thread.is_alive():
                    node_monitor_thread = threading.Thread(target=monitor_nodes, args=(job_id,), daemon=True)
                    node_monitor_thread.start()
                    print("node monitor started().")

                
            elif "state=FINISHED" in output:
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

            elif "state=WAITING" in output:
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
                update_task(job_id, task_id, state=state)

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
    print(f"Task monitor stopped fro {task_id}")
