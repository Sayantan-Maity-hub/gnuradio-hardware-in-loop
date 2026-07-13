import time
from node_registry import update_node
from ssh_client import SSHConnection
from concurrent.futures import ThreadPoolExecutor


def monitor_single_node(node, connections):
    print(f"Checking {node}")
    if node not in connections:
        print(f"Creating SSH for {node}")
        try:
            ssh = SSHConnection(node)
            print(f"Creating SSH for {node}")
            connections[node] = ssh

            return
        except Exception as e:
            print(f"SSH failed {node}: {e}")
            update_node(node, {"status": "OFFLINE", "error": str(e)})

            return
    try:
        print(f"Getting info {node}")
        ssh = connections[node]
        info = ssh.get_node_info()
        print(f"Info received {node}")
        update_node(node, info)
    except Exception as e:
        print(f"Error {node}: {e}")
        update_node(node, {"status": "OFFLINE", "error": str(e)})

        try:
            ssh.close()
        except:
            pass
        connections.pop(node, None)


def monitor_nodes(nodes, interval=30):
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
