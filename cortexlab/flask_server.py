from flask import Flask, jsonify
from registry import get_nodes

app = Flask(__name__)

@app.route("/status/nodes")
def status_nodes():
    return jsonify(get_nodes())

def start_flask():
    app.run(host="0.0.0.0", port=5678, debug=False, use_reloader=False)

# ======================TEST======================

def test_flask_server():
    get_nodes(
        "mnode14",
        {
            "hostname": "mnode14",
            "status": "ONLINE",
            "os": "Ubuntu"
        }
    )

    client = app.test_client()
    response = client.get("/status/nodes")

    assert response.status_code == 200
    data = response.get_json()

    assert "mnode14" in data
    assert data["mnode14"]["status"] == "ONLINE"
    assert data["mnode14"]["hostname"] == "mnode14"
