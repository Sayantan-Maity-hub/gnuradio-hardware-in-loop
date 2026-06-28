import re
import time

def walltime_to_seconds(walltime):
    h, m, s = map(int, walltime.split(":"))
    return h*3600 + m*60 + s

    

# Submit OAR job

def reserve_nodes(remote):
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
            "Enter required nodes name(node,node): "
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

   

    #Reservation Change option
    while True:
        print("\nGenerate OAR Command:\n")
        print(cmd)

        confirm = input("\nSubmit reservation? (y/n/edit):").lower()
        if confirm == "y":
            break
        elif confirm=="edit":
            print("\nReconfiguring reservation..\n")
            return reserve_nodes(remote)
        else:
            print("Invalid input. Type y/n/edit")

    submit_output = remote.run(cmd)

    job_match = re.search(
        r"OAR_JOB_ID=(\d+)",
        submit_output
    )

    if not job_match:
        raise RuntimeError(
            "Failed to extract job ID"
        )

    job_id = int(job_match.group(1))

    #Failure case
    if job_id < 0:
        print("\n OAR REQUES FAILED")
        print("Reason from system:\n")
        print(submit_output)
        while True:
            option = input("\nOption: retry / cancel: ").lower()
            if option == "retry":
                return reserve_nodes(remote)
            elif option == "cancel":
                raise RuntimeError("Reservation Cancelled")
            else:
                print("\nInvalid input")
    
    print(f"\nJob ID: {job_id}")

    

    job_info = remote.run(
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
    return job_id, nodes, walltime_to_seconds(walltime)

