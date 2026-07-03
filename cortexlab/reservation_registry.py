import threading
import time

reservation_registry = {}
lock = threading.Lock()
def create_reservation(job_id, username, reserevation_type, walltime, future=False, reservation_time=None, requested_nodes=None, requested_count=None, script=None, command=None):

    with lock:
        reservation_registry[job_id] = {
            "username": username,
            "job_id": job_id,
            "state": "SUBMITTED",
            "walltime": walltime,
            "reservation_Type": reserevation_type,
            "future": future,
            "reservation_time": reservation_time,
            "requested_nodes": requested_nodes or [],
            "requested_count": requested_count,
            "assigned_nodes": [],
            "scheduled_start": None,
            "wait_seconds": None,
            "scenario_generate": False,
            "scenatio_upload": False,

            "task_id": None,
            "task_state": None,

            "created_at": time.time(),
            "last_update": time.time()
        }
def update_reservation(job_id, **kwargs):

    with lock:
        if job_id in reservation_registry:
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