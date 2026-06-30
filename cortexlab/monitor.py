import time
from registry import update_node
from ssh_client import SSHConnection

def monitor_nodes(nodes, interval=30):
    connections = {}
    for node in nodes:
        try:
            ssh = SSHConnection(node)
            connections[node] = ssh
            print(f"[CONNECTED] {node}")
        except Exception as e:
            print(f"[FAILED] {node}: {e}")
    while True:
        for node in nodes:
            try:
                ssh = connections[node]
                info = ssh.get_node_info()
                update_node(node, info)
                print(f"[ONLINE] {node}")
            except Exception as e:
                update_node(node, {
                        "status": "OFFLINE",
                        "error": str(e)
                    }
                )
                print(f"[OFFLINE] {node}: {e}")
        time.sleep(10)
    