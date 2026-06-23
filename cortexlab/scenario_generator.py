import subprocess
def hostname_to_scenario_name(host):
    short=host.split(".")[0]
    return short.replace("mnode", "node")

def generate_scenario(nodes):
    scenario_nodes = []
    for host in nodes:
        scenario_name=(hostname_to_scenario_name(host))

        scenario_nodes.extend([
            f"{scenario_name}:",
            "  container:",
            "    -image: ghcr.io/cortex-lab/cxlb-gnuraio-3.10:1.5",
            "     command: /usr/sbin/sshd -p 2222 -D",

        ])
        content="\n".join([
            "description: Conroller and runner Communication Test",
            "duration: 1200",
            "",
            "nodes:",
            *scenario_nodes
        ])

        with open(
            "controller/scenario.yaml",
            "w"
        ) as f:
            f.write(content)
            
def create_task():
    subprocess.run("minus task create", shell=True, check=True)

def submit_task():
    subprocess.run(
        "minus task submit controller.task",
        shell=True,
        check=True
    )
