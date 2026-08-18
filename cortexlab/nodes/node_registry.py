import threading
import time
from ..reservation.reservation_registry import get_reservation


registry = {}
lock = threading.Lock()


def update_node(node, data=None, **kwargs):
    """
    Update information for a node.

    Supports both:

        update_node("node14", {"status": "ONLINE"})

    and:

        update_node(
            "node14",
            status="ONLINE",
            busy=True,
            experiment_id="123"
        )
    """

    # Merge dictionary + keyword arguments
    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise TypeError("data must be a dictionary")

    data = {
        **data,
        **kwargs,
    }

    with lock:

        existing = registry.get(
            node,
            {
                "hostname": node,
                "status": "UNKNOWN",
                "os": None,
                "job": {},
                "busy": False,
                "execution_id": None,
                "experiment_id": None,
            },
        )

        existing_job = existing.get("job", {})

        existing_busy = existing.get("busy", False)

        existing_execution_id = existing.get("execution_id")

        existing_experiment_id = existing.get("experiment_id")

        # Parse OS information
        os_data = data.get("os", existing.get("os", ""))

        pretty = existing.get("os")

        if isinstance(os_data, str):

            for line in os_data.splitlines():

                if line.startswith("PRETTY_NAME="):

                    pretty = line.split(
                        "=",
                        1
                    )[1].strip('"')

                    break

        # Update registry

        registry[node] = {
            "hostname": data.get("hostname", existing.get("hostname", node)),

            "status": data.get("status", existing.get("status", None)),

            "os": pretty,

            "job": data.get("job", existing_job),

            "busy": data.get("busy", existing_busy),

            "execution_id": data.get("execution_id", existing_execution_id),

            "experiment_id": data.get("experiment_id", existing_experiment_id),
        }


def update_job(node, **kwargs):

    with lock:

        if node not in registry:

            registry[node] = {
                "hostname": node,
                "status": "UNKNOWN",
                "os": None,
                "job": {},
                "busy": False,
                "execution_id": None,
                "experiment_id": None,
            }

        job = registry[node].setdefault("job", {})

        for key, value in kwargs.items():

            if value is not None:
                job[key] = value


def clear_job(node):

    with lock:

        if node in registry:
            registry[node]["job"] = {}


def get_nodes():

    with lock:
        return dict(registry)


def get_node(node):

    with lock:
        return registry.get(node)


def is_node_busy(node):

    node_info = get_node(node)

    if node_info is None:
        return False

    return node_info.get("busy", False)


def wait_for_node_status(job_id, timeout=60):

    start = time.time()

    while time.time() - start < timeout:

        reservation = get_reservation(job_id)

        if reservation is None:

            raise RuntimeError(f"Reservation {job_id} not found")

        assigned_nodes = reservation.get("assigned_nodes", [])

        node_status = reservation.get("node_status", {})

        if not assigned_nodes:

            time.sleep(1)
            continue

        # Wait until monitor has checked all nodes

        if not all(node in node_status for node in assigned_nodes):

            time.sleep(1)
            continue

        # Wait until all nodes are ONLINE

        if all(node_status.get(node) == "ONLINE" for node in assigned_nodes):

            return node_status

        time.sleep(1)

    raise TimeoutError(
        f"Assigned nodes did not become ONLINE "
        f"within {timeout} seconds"
    )