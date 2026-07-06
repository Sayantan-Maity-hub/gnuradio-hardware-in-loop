import time
from node_registry import update_node
from ssh_client import SSHConnection
from concurrent.futures import ThreadPoolExecutor

def monitor_single_node(node, connections):
    if node not in connections:
        try:
            ssh = SSHConnection(node)
            connections[node] = ssh
            print(f"[CONNECTED] {node}")
            return
        except Exception as e:
            update_node(node, {
                "status": "OFFLINE", 
                "error": str(e)
            })
            print(f"[FAILED] {node}")
            return
    try:
        ssh = connections[node]
        info = ssh.get_node_info()
        update_node(node, info)
        print(f"[ONLINE] {node}")
    except Exception as e:
        update_node(node, {
            "status": "OFFLINE",
            "error": str(e)

        })
        print(f"[OFFLINE] {node}: {e}")

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
    