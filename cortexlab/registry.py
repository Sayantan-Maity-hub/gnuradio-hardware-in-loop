import threading
registry = {}
lock = threading.Lock()
def update_node(node, data):
    with lock:
        registry[node]=data

def get_nodes():
    with lock:
        return dict(registry)
    
