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
    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    return result.stdout

# Submit OAR job
print("\n======= Submitting OAR Job =======")

print("1. Best allocation")
print("2. preferred nodes")
print("3. Future reservation")

choice = input("\nSelect option: ")

walltime = input("Enter walltime (HH:MM:SS): ")

sleep_time = input("Enter sleep time (in seconds):")

# Option - 1: Best allocation
if choice == "1":
    cmd = (f'oarsub -l nodes=BEST,walltime={walltime} "sleep {sleep_time}"')

# Option - 2: Preferred nodes
elif choice == "2":
    nodes = int(input("Enter your requred node number: "))
    required_nodes = input("Enter required nodes name: ")

    nodes_numbers = [x.strip() for x in required_nodes.split(",")]

    full_nodes = [f"mnode{n}.cortexlab.fr" for n in nodes_numbers]
    node_string = "', '".join(full_nodes)

    resource =(f'{{"network_address in (\'{node_string}\')"}}/nodes={nodes}')
    cmd = (f'oarsub -l {resource},walltime={walltime} "sleep {sleep_time}"')

# Option - 3: Future reservation
elif choice == "3":
    required_nodes = input("\nHow many nodes needed: ")
    reservation_time = input("Enter reservation time (YYYY-MM-DD HH:MM:SS):")
    cmd = (f'oarsub -l nodes={required_nodes},walltime={walltime} -r "{reservation_time}" "sleep {sleep_time}"')

else:
    print("Invalid option")
    exit(1)

#show command
print("\n Generated OAR Command:\n")
print(cmd)

confirm = input("\nSubmit reservation? (y/n): ")
if confirm.lower() != "y":
    print("Cancelled.")
    exit()

# Submit Job
submit_output = run_command(cmd)

# Extract job ID
job_match = re.search(r"OAR_JOB_ID=(\d+)", submit_output)

if not job_match:
    print("Failed to extract job ID")
    exit(1)

job_id = job_match.group(1)

print(f"\nJob ID: {job_id}")

# Wait for scheduling
time.sleep(10)

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

nodes = host_string.split("+")  # Split nodes

print("\nAllocated Nodes:")

for i, node in enumerate(nodes, start=1):
    print(f"Node {i}: {node}")


if len(nodes) >= 2:
    tx_node = nodes[int(input("Enter TX node number: "))]
    rx_node = nodes[int(input("Enter RX node number: "))]

    print(f"\nTX Node: {tx_node}")
    print(f"RX Node: {rx_node}")