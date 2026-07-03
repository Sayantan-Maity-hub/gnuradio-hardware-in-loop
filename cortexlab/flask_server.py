from flask import Flask, Response, render_template, request, jsonify
from flask_cors import CORS
from registry import get_nodes, get_node
from reservation import reserve_nodes
from reservation_monitor import reservation_monitor
from job_runner import run_job
import threading
import json


app = Flask(__name__)

CORS(app)

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/reservation/create", methods=["POST"])
def create_reserve():
    data = request.json

    try:
        job_id = reserve_nodes(
            hostname= data["hostname"],
            username = data["username"],
            reservation_type = data["reservation_type"],
            walltime = data["walltime"],
            future = data["future"],
            reservation_time = data.get("reservatoion_time"),
            preferred_nodes=data.get("prefered_nodes"),           
        )
        if job_id:

            reservation_thread = threading.Thread(target=reservation_monitor, daemon=True)
            reservation_thread.start()
            print("[OK] Reservation monitor started....")

        
        return jsonify({"job_id": job_id})
    except Exception as e:
        return jsonify({
            "success": False,
            "retry_allowed": True,

            "error": {e}
        }), 400
    
    


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
@app.route("/status/job/<node>")
def job_status(node):
    node_data = get_node(node)
    if not node_data:
        return {"error": "node not found"}, 404
    return node_data.get("job", {})


def start_flask():
    app.run(host="0.0.0.0", port=5678, debug=False, use_reloader = False)


