import time
from concurrent.futures import ThreadPoolExecutor

from .node_registry import update_node
from ..reservation.reservation_registry import (
    get_all_reservation,
    get_reservation,
    update_reservation,
)
from ..remote_connections.ssh_connection import SSHConnection


def monitor_single_node(node, connections):

    if node not in connections:

        try:
            ssh = SSHConnection(node)

            connections[node] = ssh
        except Exception as e:

            update_node(node, {"status": "OFFLINE", "error": str(e)})

            reservations = get_all_reservation()

            for job_id, reservation in reservations.items():
                if node in reservation.get("assigned_nodes", []):
                    node_status = reservation.setdefault("node_status", {})
                    node_status[node] = "OFFLINE"

                    update_reservation(job_id, node_status=node_status)

            connections.pop(node, None)

    try:

        ssh = connections[node]
        info = ssh.get_node_info()

        # Update node status in the node registry
        update_node(node, info)

        # Update Node status in Reservation registry
        reservations = get_all_reservation()
        for job_id, reservation in reservations.items():
            if node in reservation.get("assigned_nodes", []):
                node_status = reservation.setdefault("node_status", {})
                node_status[node] = info.get("status", "OFFLINE")

                update_reservation(job_id, node_status=node_status)
    except Exception as e:

        update_node(node, {"status": "OFFLINE", "error": str(e)})

        try:
            ssh.close()
        except Exception as close_exception:
            print(f"Failed closing SSH for {node}: {close_exception}")
        connections.pop(node, None)


def monitor_nodes(job_id):
    interval = 1

    reservation = get_reservation(job_id)
    nodes = reservation["assigned_nodes"]

    print(f"monitor nodes: {nodes}")
    connections = {}
    executor = ThreadPoolExecutor(max_workers=max(1, len(nodes)))
    while True:
        futures = []

        for node in nodes:
            future = executor.submit(monitor_single_node, node, connections)
            futures.append(future)

        for future in futures:
            future.result()
        time.sleep(interval)
