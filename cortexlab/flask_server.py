from flask import Flask, jsonify
from registry import get_nodes, update_node

app = Flask(__name__)

@app.route("/status/nodes")
def status_nodes():
    return jsonify(get_nodes())

def start_flask():
    app.run(host="0.0.0.0", port=5678, debug=False, use_reloader=False)

