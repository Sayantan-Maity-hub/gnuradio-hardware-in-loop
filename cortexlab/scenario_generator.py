import yaml
import time

def generate_scenario(nodes, walltime):
    description = input("Enter Test Description: \n")
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

    with open("cortexlab/scenario/scenario.yaml","w") as f:
        yaml.dump(scenario, f, sort_keys=False)

def create_task(remote):
    output = remote.run("minus task create -f scenario")
    print (output)

def submit_task(remote):
    output = remote.run(
        "minus task submit scenario.task")
    print(f"taskId: {output}")
    return output



def wait_for_task_running(remote, task_id):
    print(f"Waiting for task {task_id} to start...")

    while True:
        output = remote.run(f"minus task info {task_id}")

        if "state=RUNNING" in output:
            print("Task is RUNNING → nodes are ready")
            return

        if "state=ERROR" in output or "aborted=True" in output:
            print(output)
            raise Exception("Task failed")

        print("Still waiting...")
        time.sleep(5)

