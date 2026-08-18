from cortexlab.nodes.node_registry import update_node, get_nodes


# ======================TEST======================
def test_registry():
    print("\n[TEST] Registry update Test")
    update_node("node14", {"status": "ONLINE"})

    nodes = get_nodes()
    assert "node14" in nodes
    assert nodes["node14"]["status"] == "ONLINE"
    print("[PASS] registry.py")
