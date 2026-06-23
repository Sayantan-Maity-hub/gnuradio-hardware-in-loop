import time
from registry import update_node
from ssh_client import get_node_info

def monitor_nodes(nodes, interval=30):
    while True:
        for node in nodes:
            try:
                info =get_node_info(node)
                update_node(node, info)
                print(f"[ONLINE] {node}")
            except Exception as e:
                update_node(node, {"status": "OFFLINE", "error": str(e)})
                print(f"[OFFLINE] {node}")
            
            time.sleep(interval)