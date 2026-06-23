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

def reserve_nodes():
    print("\n======= Submitting OAR Job =======")

    print("1. Best allocation")
    print("2. Preferred nodes")
    print("3. Future reservation")

    choice = input("\nSelect option: ")

    walltime = input(
        "Enter walltime (HH:MM:SS): "
    )

    sleep_time = input(
        "Enter sleep time (in seconds): "
    )

    # Option 1
    if choice == "1":

        cmd = (
            f'oarsub -l nodes=BEST,walltime={walltime} '
            f'"sleep {sleep_time}"'
        )

    # Option 2
    elif choice == "2":

        nodes = int(
            input(
                "Enter your required node number: "
            )
        )

        required_nodes = input(
            "Enter required nodes name: "
        )

        nodes_numbers = [
            x.strip()
            for x in required_nodes.split(",")
        ]

        full_nodes = [
            f"mnode{n}.cortexlab.fr"
            for n in nodes_numbers
        ]

        node_string = "', '".join(
            full_nodes
        )

        resource = (
            f'{{"network_address in (\'{node_string}\')"}}'
            f'/nodes={nodes}'
        )

        cmd = (
            f'oarsub -l {resource},walltime={walltime} '
            f'"sleep {sleep_time}"'
        )

    # Option 3
    elif choice == "3":

        required_nodes = input(
            "\nHow many nodes needed: "
        )

        reservation_time = input(
            "Enter reservation time "
            "(YYYY-MM-DD HH:MM:SS): "
        )

        cmd = (
            f'oarsub -l nodes={required_nodes},'
            f'walltime={walltime} '
            f'-r "{reservation_time}" '
            f'"sleep {sleep_time}"'
        )

    else:
        raise ValueError(
            "Invalid option"
        )

    print("\nGenerated OAR Command:\n")
    print(cmd)

    confirm = input(
        "\nSubmit reservation? (y/n): "
    )

    if confirm.lower() != "y":
        raise RuntimeError(
            "Reservation cancelled"
        )

    submit_output = run_command(cmd)

    job_match = re.search(
        r"OAR_JOB_ID=(\d+)",
        submit_output
    )

    if not job_match:
        raise RuntimeError(
            "Failed to extract job ID"
        )

    job_id = job_match.group(1)

    print(f"\nJob ID: {job_id}")

    time.sleep(10)

    job_info = run_command(
        f"oarstat -fj {job_id}"
    )

    print("\nJob Info:")
    print(job_info)

    host_match = re.search(
        r"assigned_hostnames\s*=\s*(.+)",
        job_info
    )

    if not host_match:
        raise RuntimeError(
            "Failed to extract hostnames"
        )

    host_string = (
        host_match.group(1)
        .strip()
    )

    nodes = host_string.split("+")

    print("\nAllocated Nodes:")

    for node in nodes:
        print(node)

def walltime_to_seconds(walltime):
    h, m, s = map(int, walltime.split(":"))
    return h*3600 + m*60 + s

    return job_id, nodes, walltime_to_seconds(walltime)