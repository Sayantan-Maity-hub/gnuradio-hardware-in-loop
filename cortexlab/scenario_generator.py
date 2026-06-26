import yaml
def hostname_to_scenario_name(host):
    short=host.split(".")[0]
    return short.replace("mnode", "node")

def generate_scenario(nodes, walltime):
    scenario = {
        "description": "Controller Test",
        "duration": walltime,
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

    with open("cortexlab/scenario/scenario.yaml","w") as f:
        yaml.dump(scenario, f, sort_keys=False)

def create_task(remote):
    output = remote.run("minus task create scenario")
    print (output)

def submit_task(remote):
    output = remote.run(
        "minus task submit scenario.task")
    print(output)

# ===================================== TEST===========================================

def test_scenario_generation():
    nodes = ["mnode14.cortexlab.fr", "mnode21.cortexlab.fr"]

    generate_scenario(nodes, 600)

    with open("cortexlab/scenario/scenario.yaml") as f:
        data = yaml.safe_load(f)
    assert data["description"] == "Controller Test"
    assert len(data["nodes"]) == 2

