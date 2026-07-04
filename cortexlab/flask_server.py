from flask import Flask, Response, render_template, request, jsonify
from flask_cors import CORS
from registry import get_nodes, get_node
from reservation import reserve_nodes
from reservation_monitor import reservation_monitor
from scenario_generator import generate_scenario, minus_create_task, minus_submit_task
from cortexlab_remote import cortexlab_Remote
from reservation_registry import get_all_reservation, get_reservation, update_reservation
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
            preferred_nodes=data.get("preferred_nodes", []),           
        )
        reservation_monitor();
        return jsonify({
            "job_id": job_id
            
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "retry_allowed": True,

            "error": str(e)
        }), 400

@app.route("/status/reservations")
def reservation_status():
    return jsonify(list(get_all_reservation().values()))

@app.route("/task/create", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "message": "No requese data received"
        }), 400
    job_id = int(data.get("job_id"))
    if not job_id:
        return jsonify({
            "success": False,
            "message": "job_id missing"
        })
    reservation = get_reservation(job_id)
    print("Reservation:", reservation)

    
    
    task_description = data.get("task_description", "")
    print("Received data:", data)
    print("Job ID:", job_id)

    if reservation is None:
        return jsonify({
            "success": False,
            "message": f"Reservation {job_id} not found or has already finished."
        }),     404

    
    nodes = reservation["assigned_nodes"]
    
    walltime = reservation["walltime"]


    generate_scenario(job_id, nodes, walltime, task_description)
    remote = cortexlab_Remote()
    local_folder = str(f"cortexlab/{job_id}")
    remote_folder = str(job_id)
    remote.upload_folder(local_folder, remote_folder)
    minus_create_task(remote, remote_folder)
    task_id = minus_submit_task(remote, remote_folder)
    update_reservation(job_id=job_id, task_id=task_id)

    return jsonify({
        "success": True,
        "task_id": task_id
    })


    


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


