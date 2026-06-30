import re
from registry import update_job
from ssh_client import SSHConnection

def run_job(node, script_path):
    remote_path = f"/tmp/{script_path.split('/')[1]}"

    ssh = SSHConnection(node)

    print(f"{node} --> Job Assigned")
    update_job(node = node, job_name = script_path, state = "ASSIGNED")
    
    
    #upload script:
    print(f"{node} --> Uploading script...")
    ssh.upload_file(script_path, remote_path)

    #make script executable:
    print(f"{node} --> Preparing script permisssion")
    ssh.run_on_node(f"chmod +x {remote_path}")

    #job running..
    print(f"{node} --> Job Running...")
    update_job(node=node, job_name = script_path, state = "RUNNING")

    output = ssh.run_on_node(f"bash {remote_path}")
    steps = []
    for line in output.splitlines():
        match = re.match(r"::STATUS:(.*?):(PASS|FAIL):", line)
        if match:
            steps.append({"name": match.group(1), "result": match.group(2)})

    print(f"{node} --> Job Finished...")

    update_job(node = node, job_name=script_path, state="FINISHED", steps=steps)

    return output
