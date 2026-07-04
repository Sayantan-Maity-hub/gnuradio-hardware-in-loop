import yaml
import time
import os
import cortexlab_remote
from reservation_registry import update_reservation

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



def wait_for_task_running(remote, job_id, task_id):
    print(f"Waiting for task {task_id} to start...")

    while True:
        output = remote.run(f"minus task info {task_id}")

        if "state=RUNNING" in output:
            print("Task is RUNNING at nodes are ready")
            update_reservation(job_id, task_state = "RUNNING")

            return

        if "state=ERROR" in output or "aborted=True" in output:
            print(output)
            raise Exception("Task failed")

        print("Still waiting...")
        time.sleep(5)


