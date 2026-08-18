import threading
import time

reservation_registry = {}
lock = threading.Lock()


def create_reservation(job_id, username, walltime, reservation_name, reservation_time=None):

    with lock:
        reservation_registry[job_id] = {
            "username": username,
            "reservation_name": reservation_name,
            "job_id": job_id,
            "state": "SUBMITTED",
            "walltime": walltime,
            "reservation_time": reservation_time,
            "assigned_nodes": [],
            "node_status": {},
            "scheduled_start": None,
            "waiting_time": None,
            "scenario_generate": False,
            "scenatio_upload": False,
            "tasks": [],
            "created_at": time.time(),
            "last_update": time.time(),
        }


def update_reservation(job_id, **kwargs):

    with lock:
        if job_id not in reservation_registry:
            return

        reservation_registry[job_id].update(kwargs)
        reservation_registry[job_id]["last_update"] = time.time()


def get_reservation(job_id):
    with lock:
        return reservation_registry.get(job_id)


def get_all_reservation():
    with lock:
        return reservation_registry.copy()


def delete_reservation(job_id):
    with lock:
        reservation_registry.pop(job_id, None)
