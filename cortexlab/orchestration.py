import subprocess
import re
import time

def run_command(cmd):
    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True
    )

    return result.stdout

# Submit OAR job
submit_output = run_command(
    'oarsub -l nodes=2,walltime=0:05:00 "sleep 300"'
)

print("Submission Output:")
print(submit_output)

# Extract job ID
job_match = re.search(r"OAR_JOB_ID=(\d+)", submit_output)

if not job_match:
    print("Failed to extract job ID")
    exit(1)

job_id = job_match.group(1)

print(f"\nJob ID: {job_id}")

# Wait for scheduling
time.sleep(5)

# Get full job info
job_info = run_command(f"oarstat -fj {job_id}")

print("\nJob Info:")
print(job_info)

# Extract assigned hostnames
host_match = re.search(
    r"assigned_hostnames\s*=\s*(.+)",
    job_info
)

if not host_match:
    print("Failed to extract hostnames")
    exit(1)

host_string = host_match.group(1).strip()

# Split nodes
nodes = host_string.split("+")

print("\nAllocated Nodes:")

for i, node in enumerate(nodes, start=1):
    print(f"Node {i}: {node}")

# Assigned the node 
if len(nodes) >= 2:
    tx_node = nodes[0]
    rx_node = nodes[1]

    print(f"\nTX Node: {tx_node}")
    print(f"RX Node: {rx_node}")
