import yaml
import time
import os

def generate_scenario(job_id, nodes, walltime, description):
    scenario = {
        "description": f"{description}",
        "duration": walltime,
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

    os.makedirs(f"cortexlab/{job_id}", exist_ok=True)

    with open(f"cortexlab/{job_id}/scenario.yaml","w") as f:
        yaml.dump(scenario, f, sort_keys=False)

def create_task(remote, folder_path):
    output = remote.run(f"minus task create -f {folder_path}")
    print (output)

def submit_task(remote, folder_path):
    output = remote.run(f"minus task submit {folder_path}.task")
    print(f"taskId: {output}")
    return output



def wait_for_task_running(remote, task_id):
    print(f"Waiting for task {task_id} to start...")

    while True:
        output = remote.run(f"minus task info {task_id}")

        if "state=RUNNING" in output:
            print("Task is RUNNING â†’ nodes are ready")
            return

        if "state=ERROR" in output or "aborted=True" in output:
            print(output)
            raise Exception("Task failed")

        print("Still waiting...")
        time.sleep(5)


