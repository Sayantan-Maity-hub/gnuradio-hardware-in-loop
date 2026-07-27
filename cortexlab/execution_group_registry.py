import threading
import time
from copy import deepcopy


execution_groups = {}
lock = threading.Lock()
next_group_id = 1


def create_execution_group(job_id, task_id, name, nodes, folder):
    """Create an execution group and return its ID."""
    global next_group_id

    with lock:
        group_id = next_group_id
        next_group_id += 1

        execution_groups[group_id] = {
            "group_id": group_id,
            "job_id": job_id,
            "task_id": task_id,
            "name": name,
            "nodes": list(nodes),
            "folder": folder,
            "state": "CREATED",
            "sync_state": "WAITING_FOR_UPLOADS",
            "execution_ids": {},
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "started_at": None,
            "finished_at": None,
        }
        return group_id


def get_execution_group(group_id):
    with lock:
        group = execution_groups.get(group_id)
        return deepcopy(group) if group else None


def update_execution_group(group_id, **kwargs):
    with lock:
        if group_id not in execution_groups:
            return False
        execution_groups[group_id].update(kwargs)
        return True


def add_node_execution(group_id, node, execution_id):
    with lock:
        group = execution_groups.get(group_id)
        if group is None:
            return False
        group["execution_ids"][node] = execution_id
        return True


def get_all_execution_groups():
    with lock:
        return deepcopy(execution_groups)


def get_active_node_conflicts(nodes):
    """Return active groups that already own one or more requested nodes."""
    requested = set(nodes)
    terminal_states = {"FINISHED", "FAILED", "CANCELLED"}

    with lock:
        return [
            group_id
            for group_id, group in execution_groups.items()
            if group["state"] not in terminal_states
            and requested.intersection(group["nodes"])
        ]
