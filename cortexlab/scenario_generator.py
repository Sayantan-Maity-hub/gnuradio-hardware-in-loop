import yaml
import time
import os
import cortexlab_remote
from reservation_registry import update_reservation, get_reservation

def generate_scenario(scenario_folder, nodes, duration, task_description):

    scenario = {
        "description": f"{task_description}",
        "duration": duration,
        "nodes": {}

    }
    
    scenario_nodes = []
    for host in nodes:
        node_name= host

        scenario["nodes"][node_name] = {
            "container": [
                {
                    "image": "ghcr.io/cortexlab/cxlb-gnuradio-3.10:1.5",
                    "command": "/usr/sbin/sshd -p 2222 -D"
                }

            ]
        }

    os.makedirs(scenario_folder, exist_ok=True)

    with open(os.path.join(scenario_folder, "scenario.yaml"), "w") as f:
        yaml.dump(scenario, f, sort_keys=False)
        print("Scenario generation successfull")



def minus_create_task(remote, remote_folder):
    output = remote.run(f"minus task create -f {remote_folder}")
    print (output)


def minus_submit_task(remote, remote_folder):
    output = remote.run(f"minus task submit {remote_folder}.task")
    print(f"taskId: {output}")
    return output



def update_task_status(remote, job_id, task_id):
    print(f"update the task status...")

    output = remote.run(f"minus task info {task_id}")
    print(output)
    if "state=RUNNING" in output:
        state = "RUNNING"

    elif "state=FINISHED"  in output:
        state = "FINISHED"

    elif "state=ERROR" in output:
        state = "ERROR"

    elif "state=WAITING"in output:
        state = "WAITING"
    
    else:
        state = "UNKNOWN"

    reservation = get_reservation(job_id)

    for task in reservation["tasks"]:
        if task["task_id"] == task_id:
            task["state"] = state
            break
    
    update_reservation(job_id, tasks=reservation["tasks"])

    return state


