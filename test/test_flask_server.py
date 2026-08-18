from cortexlab.flask_server import app
from cortexlab.nodes.node_registry import update_node

# ======================TEST======================


def test_flask_server():
    print("\n[TEST] Flask Server Test")
    update_node("mnode14", {"hostname": "mnode14", "status": "ONLINE", "os": "Ubuntu"})

    client = app.test_client()
    response = client.get("/status/nodes")

    assert response.status_code == 200
    data = response.get_json()

    assert "mnode14" in data["data"]
    assert data["data"]["mnode14"]["status"] == "ONLINE"
    assert data["data"]["mnode14"]["hostname"] == "mnode14"
