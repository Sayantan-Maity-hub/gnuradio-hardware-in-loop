import threading
registry = {}
lock = threading.Lock()
def update_node(node, data):
    with lock:
        os_data = data.get("os", "")
        pretty = None
        if isinstance(os_data, str):
                    for line in os_data.splitlines():
                         if line.startswith("PRETTY_NAME="):
                              pretty = line.split("=", 1)[1].strip('"')
                              break

        registry[node]={
            "hostname": data.get("hostname"),
            "status": data.get("status"),
            "os": pretty
        }
    # Notify  clients after releasing the lock
def get_nodes():
    with lock:
        return dict(registry)
    
