import re
import time
from datetime import datetime
from cortexlab_remote import cortexlab_Remote
from reservation_registry import create_reservation
import config

VALID_NODES = [2, 4, 6, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 34, 36, 37, 38]

def walltime_to_seconds(walltime):
    h, m, s = map(int, walltime.split(":"))
    return h*3600 + m*60 + s

    

# Submit OAR job

def reserve_nodes(hostname, username, reservation_type, walltime, future=False, reservation_time = None, preferred_nodes=None, script=None):

    
    print("\n======= Submitting OAR Job =======")
    config.USERNAME = username
    config.HOSTNAME = hostname

    remote = cortexlab_Remote()

    try:
        walltime_to_seconds(walltime)
    except Exception:
        raise ValueError("walltime must be HH:MM:SS")
    
    sleep_time = (walltime_to_seconds(walltime)+60)
    
    #BEST Allocation
    if reservation_type == "best":
        resource = f"node=BEST, walltime={walltime}"
        requested_nodes = []
    

    # PREFERRED Alocation
    elif reservation_type == "preferred":
        node_count = len(preferred_nodes)
        if not node_count:
                    raise ValueError("node_count required")
                    print("Invalid input. Please enter a positive and valid node number (1-40).")
        if not preferred_nodes:
                raise ValueError("preferred node reqired")
        if not all(n in VALID_NODES for n in preferred_nodes):
                raise ValueError(
                    f"Invalid node selected."
                    f"Valid nodes: {VALID_NODES}"
                )
                print("Invalid input. Please enter a valid integer.")
        nodes_numbers = []
        full_nodes = [
            f"mnode{n}.cortexlab.fr"
            for n in nodes_numbers
        ]

        node_string = "', '".join(
            full_nodes
        )

        resource = (
            f'{{"network_address in (\'{node_string}\')"}}'
            f'/nodes={node_count},'
            f'walltime={walltime}'
        )
        required_nodes = preferred_nodes

    else:
         raise ValueError("Unknown reservation type")

    
    #Build OAR command
    cmd = f'oarsub -l {resource}'

    if future:
         if not reservation_time:
              raise ValueError("reservation_time required")
         try:
              datetime.strptime(reservation_time, "%Y-%m-%d %H:%M:%S")
         except ValueError:
              raise ValueError("reservation_time must be YYYY-MM-DD HH:MM:SS")
         cmd += (f'-r "res{reservation_time}" ')
    cmd+= f'"sleep {sleep_time}"'

    print("\nGenerate OAR Command:\n")
    print(cmd)

    submit_output = remote.run(cmd)

    job_match = re.search(
        r"OAR_JOB_ID=(\d+)",
        submit_output
    )

    if not job_match:
        raise RuntimeError(
            f"Failed to extract job ID\n"
            f"{submit_output}"
        )

    job_id = int(job_match.group(1))

    #Failure case
    if job_id < 0:
        raise RuntimeError(
            f"OAR request failed:\n{submit_output}"
    )

    print(f"\nJob ID: {job_id}")

    #store initial data in registry
    create_reservation(
         job_id = job_id,
         username=username,
         reservation_type = reservation_type,
         wallttime = walltime,
         future = future,
         reservation_time = reservation_time,
         requested_nodes = requested_nodes,
         requested_node_no = node_count,
         script=script,
         command = cmd
        )
    print(f"\nReservation submitted successfully")

    return job_id


