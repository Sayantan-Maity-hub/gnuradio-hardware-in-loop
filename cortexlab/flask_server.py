from flask import Flask, jsonify
from flask_socketio import SocketIO
from registry import get_nodes, update_node

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

@app.route("/status/nodes")

def status_nodes():
    return jsonify(get_nodes())


socketio = SocketIO(app)

def start_flask():
    socketio.run(app, host="0.0.0.0", port=5678, debug=False)

