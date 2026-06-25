import threading
registry = {}
lock = threading.Lock()
def update_node(node, data):
    with lock:
        registry[node]=data

def get_nodes():
    with lock:
        return dict(registry)
    
# ======================TEST======================
def test_registry():
    update_node("node14", {"status": "ONLINE"})

    nodes = get_nodes()
    assert "node14" in nodes
    assert nodes["node14"]["status"] == "ONLINE"
    