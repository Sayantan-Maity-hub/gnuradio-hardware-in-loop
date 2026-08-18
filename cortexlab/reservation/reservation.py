import re
from datetime import datetime

from ..remote_connections.cortexlab_remote import cortexlab_Remote
from .reservation_registry import create_reservation, get_reservation
import config


def walltime_to_seconds(walltime):
    h, m, s = map(int, walltime.split(":"))
    return h * 3600 + m * 60 + s


# Submit OAR job


def reserve_nodes(hostname, username, walltime, reservation_name):

    print("\n======= Submitting OAR Job =======")

    #Controller credentials
    if username:
        config.USERNAME = username

    if hostname:     
        config.HOSTNAME = hostname

    if not config.USERNAME or not config.HOSTNAME:
        raise ValueError("Controller hostname and username must be configured")

    remote = cortexlab_Remote()

    try:
        walltime_to_seconds(walltime)
    except Exception:
        raise ValueError("walltime must be HH:MM:SS")

    sleep_time = walltime_to_seconds(walltime) + 60
    preferred_nodes = config.CORTEXLAB_VALID_NODES
    node_count = len(preferred_nodes)

    full_nodes = [f"mnode{n}.cortexlab.fr" for n in preferred_nodes]

    node_string = "', '".join(full_nodes)

    resource = (
        f"{{\"network_address in ('{node_string}')\"}}"
        f"/nodes={node_count},"
        f"walltime={walltime}"
    )

    # Build OAR command
    cmd = f"oarsub -l {resource} 'sleep {sleep_time}'"
    print(f"\nSubmitting OAR job with command:\n{cmd}")

    # Submit the job and capture the output
    submit_output = remote.run(cmd)

    job_match = re.search(r"OAR_JOB_ID=(\d+)", submit_output)

    if not job_match:
        raise RuntimeError(f"Failed to extract job ID\n" f"{submit_output}")

    job_id = int(job_match.group(1))

    # Failure case
    if job_id < 0:
        raise RuntimeError(f"OAR request failed:\n{submit_output}")

    print(f"\nJob ID: {job_id}")

    # store initial data in registry
    create_reservation(
        job_id=job_id,
        username=username,
        walltime=walltime,
        reservation_name=reservation_name
    )
    print(f"\nReservation submitted successfully")
    print(get_reservation(job_id))

    return job_id
