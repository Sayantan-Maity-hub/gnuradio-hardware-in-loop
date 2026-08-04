import yaml
import time
import os
from cortexlab_remote import cortexlab_Remote
from reservation_registry import update_reservation, get_reservation
import threading
from minus_task_monitor import minus_task_monitor


def generate_scenario(scenario_folder, nodes, duration, task_description):

    scenario = {"description": f"{task_description}", "duration": duration, "nodes": {}}

    scenario_nodes = []
    for host in nodes:
        node_name = f"node{host}"

        scenario["nodes"][node_name] = {
            "container": [
                {
                    "image": "ghcr.io/cortexlab/cxlb-gnuradio-3.10:1.5",
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
    
            state = reservation["state"].lower()
    
            # Wait until reservation is ready
            if state != "running":
                time.sleep(2)
                continue
            remote = cortexlab_Remote()
            try:
                 output = remote.run(f"minus task create -f '{remote_folder}'")
                 print(output)
                 return
            finally:
                 remote.close()


def minus_submit_task(job_id, remote_folder):

        remote = cortexlab_Remote()
        try:
            output = remote.run(f"minus task submit {remote_folder}.task")
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