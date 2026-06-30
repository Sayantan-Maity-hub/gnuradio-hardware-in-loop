import re
from registry import update_job
from ssh_client import SSHConnection

def run_job(node, script_path):
    print(f"{node} --> Job Assigned")
    update_job(node = node, job_name = script_path, state = "ASSIGNED")
    ssh = SSHConnection(node)
    print(f"{node} --> Preparing script permisssion")
    ssh.run_on_node(f"chomd +x {script_path}")
    print(f"{node} --> Job Running...")
    update_job(node=node, job_name = script_path, state = "RUNNING")

    output = ssh.run_on_node(f"bash {script_path}")
    steps = []
    for line in output.splitlines():
        match = re.match(r"::STATUS:(.*?):(PASS|FAIL):", line)
        if match:
            steps.append({"name": match.group(1), "result": match.group(2)})

    print(f"{node} --> Job Finished...")

    update_job(node = node, job_name=script_path, state="FINISHED", steps=steps)

    return output
