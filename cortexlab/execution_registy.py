import threading
import time

execution_registry = {}
lock = threading.Lock()

next_execution_id = 1


def create_execution(job_id, task_id, node, folder, script, runner, group_id=None):
    global next_execution_id
    with lock:
        execution_id = next_execution_id
        next_execution_id += 1

        execution_registry[execution_id] = {
            "job_id": job_id,
            "task_id": task_id,
            "group_id": group_id,
            "node": node,
            "script": script,
            "folder": folder,
            "runner": runner,
            "state": "STARTING",
            "result": None,
            # Structured result emitted by the experiment script.  This stays
            # separate from the controller-level PASS/FAILED result above.
            "experiment_result": None,
            "stdout": "",
            "stderr": "",
            "log_path": None,
            # Set only when this node leaves synchronization and starts running.
            "execution_started_at": None,
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ended": None,
        }
        return execution_id


def update_execution(execution_id, **kwargs):
    with lock:
        if execution_id not in execution_registry:
            return False
        execution_registry[execution_id].update(kwargs)
        return True


def clear_execution(execution_id):
    with lock:
        execution_registry[execution_id] = {execution_registry.pop(execution_id, None)}


def get_execution(execution_id):
    with lock:
        return execution_registry.get(execution_id)


def get_all_execution():
    with lock:
        return dict(execution_registry)
