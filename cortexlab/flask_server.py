from flask import Flask, Response
from registry import get_nodes
import json

app = Flask(__name__)

@app.route("/status/nodes")

def status_nodes():
    return Response(json.dumps(get_nodes(), indent = 4), mimetype="application/json")

def start_flask():
    app.run(host="0.0.0.0", port=5678, debug=False, use_reloader = False)

