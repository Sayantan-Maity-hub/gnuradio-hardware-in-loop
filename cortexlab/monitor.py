import time
from registry import update_node
from ssh_client import SSHConnection
from flask_server import socketio

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
                socketio.emit(
                    "node_updat",
                    {
                        "node": node,
                        "data": info
                    }
                )
                update_node(node, info)
                print(f"[ONLINE] {node}")
            except Exception as e:
                offline_data = {
                    "hostname": node.split(".")[0],
                    "status": "OFFLINE",
                    "os": None
                }
                update_node(node, offline_data)
                socketio.emit(
                    "node_update",
                    {
                        "node": node,
                        "data": offline_data
                    }
                )
                print(f"[OFFLINE] {node}: {e}")
        time.sleep(interval)