from flask import Flask, Response, render_template, request
from flask_cors import CORS
from registry import get_nodes, get_node
from job_runner import run_job
import threading
import json


app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/status/nodes")
def status_nodes():
    return Response(json.dumps(get_nodes(), indent = 4), mimetype="application/json")

@app.route("/control/job/start", methods = ["POST"])
def start_job():
    data = request.json
    node = data.get("node")
    script = data.get("script")
    if not node or not script:
        return {"error": "node and script requireds"}, 400 
    thread = threading.Thread(target = run_job, args=(node, script))
    thread.start()

    return {
        "message": "Job started", "node": node, "script": script
    }
@app.route("/status/job/<node>"):
def job_status(node):
    node_data = get_node(node)
    if not node_data:
        return {"error": "node not found"}, 404
    return node_data.get("job", {})


def start_flask():
    app.run(host="0.0.0.0", port=5678, debug=False, use_reloader = False)

