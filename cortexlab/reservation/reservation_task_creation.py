import yaml
import time
import os
import re
from ..remote_connections.cortexlab_remote import cortexlab_Remote
from .reservation_registry import update_reservation, get_reservation
import threading
from cortexlab.reservation.minus_task_monitor import minus_task_monitor
from cortexlab.reservation.reservation import walltime_to_seconds


def generate_scenario(scenario_folder, nodes, duration, task_description, docker_image):

    scenario = {"description": f"{task_description}", "duration": duration, "nodes": {}}

    scenario_nodes = []
    for host in nodes:
        # Existing callers pass either OAR node numbers or names such as
        # ``node14``/``mnode14.cortexlab.fr``.
        match = re.search(r"(?:m?node)?(\d+)", str(host))
        if not match:
            raise ValueError(f"Invalid CortexLab node: {host}")
        node_name = f"node{match.group(1)}"

        scenario["nodes"][node_name] = {
            "container": [
                {
                    "image": docker_image,
                    "command": "/usr/sbin/sshd -p 2222 -D",
                }
            ]
        }

    os.makedirs(scenario_folder, exist_ok=True)

    with open(os.path.join(scenario_folder, "scenario.yaml"), "w") as f:
        yaml.dump(scenario, f, sort_keys=False)
        print("Scenario generation successfull")


def minus_create_task(remote_folder, job_id):
    while True:
            reservation = get_reservation(job_id)
    
            if reservation is None:
                return
            
            remote = cortexlab_Remote()
            try:
                 stdout, stderr = remote.run(f"minus task create -f '{remote_folder}'")
                 output = stdout.read().decode()
                 
                 print(output)

                 return
            finally:
                 remote.close()


def minus_submit_task(job_id, remote_folder):

        remote = cortexlab_Remote()
        try:
            stdout, stderr = remote.run(f"minus task submit {remote_folder}.task")

            output = stdout.read().decode()

        finally:
             
             remote.close()

        task_id = output.strip()

            # Update the task entry
        reservation = get_reservation(job_id)

        for task in reservation["tasks"]:
            if task["folder"] == remote_folder:
                task["task_id"] = task_id
                task["state"] = "SUBMITTED"
                break

        update_reservation(job_id, tasks=reservation["tasks"])

        threading.Thread(
            target=minus_task_monitor,
            args=(job_id, task_id),
            daemon=True,
        ).start()
        return task_id

def create_task_for_reservation(job_id):

     reservation = get_reservation(job_id)

     if reservation is None:
          raise RuntimeError(f"Reservation {job_id} not found")


     # Wait until the reservation is in the "running" state before proceeding
     print(f"waiting for reservation {job_id} to be in the 'running' state.")
     while True:
          state = reservation["state"]
          if state != "Running":
               
               print(f"waiting time {reservation["waiting_time"]} minute.")
               time.sleep(2)
               continue
          else:
               break
     nodes = reservation.get("assigned_nodes", [])

     if not nodes:
          raise RuntimeError(f"No assigned nodes found for reservation {job_id}")

     # artifact for scenario generation
     task_description = reservation["reservation_name"]
     safe_desc = re.sub(r"[^a-zA-Z0-9_-]", "_", task_description.strip())
     local_folder = os.path.join(str(job_id), safe_desc)
     remote_folder = f"{job_id}/{safe_desc}"
     nodes = reservation["assigned_nodes"]
     duration = walltime_to_seconds(reservation["walltime"])

     # Function call for scenario generationa
     generate_scenario(local_folder, nodes, duration, task_description)

     # Uploading the scenario to remote server and creating and submitting the task.
     remote = cortexlab_Remote()
     try:
          remote.upload_folder(local_folder, remote_folder)
     finally:
          remote.close()

     # Function call for creating and submitting the task.
     minus_create_task(remote_folder, job_id)
     task_id = minus_submit_task(job_id, remote_folder)

     reservation = get_reservation(job_id)

     tasks = reservation.get("tasks", [])

     task_entry = {
        "task_id": task_id,
        "description": task_description,
        "state": "CREATED",
        "folder": remote_folder,
        }

     tasks.append(task_entry)

     #update the reservation with the new task entry
     update_reservation(job_id, tasks=tasks,)

     return task_id

