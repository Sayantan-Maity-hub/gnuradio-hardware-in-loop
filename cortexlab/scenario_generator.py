import subprocess
import yaml
def hostname_to_scenario_name(host):
    short=host.split(".")[0]
    return short.replace("mnode", "node")

def generate_scenario(nodes, walltime):
    scenario = {
        "description": "Controller Test",
        "duration": {walltime},
        "nodes": {}

    }
    
    scenario_nodes = []
    for host in nodes:
        node_name=(hostname_to_scenario_name(host))

        scenario["nodes"][node_name] = {
            "container": [
                {
                    "image": "ghcr.io/cortexlab/cxlb-gnuradio-3.10:1.5",
                    "command": "/usr/sbin/sshd -p 2222 -D"
                }

            ]
        }

        with open("controller/scenario.yaml","w") as f:
            yaml.dump(scenario, f, sort_key=False)

def create_task():
    subprocess.run("minus task create controller", shell=True, check=True)

def submit_task():
    subprocess.run(
        "minus task submit controller.task",
        shell=True,
        check=True
    )
