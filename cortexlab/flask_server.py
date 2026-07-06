from flask import Flask, Response, render_template, request, jsonify
from flask_cors import CORS
from node_registry import get_nodes, get_node, update_job
from reservation import reserve_nodes, walltime_to_seconds
from reservation_monitor import reservation_monitor
from minus_task_monitor import minus_task_monitor
from monitor_nodes import monitor_nodes
from scenario_generator import generate_scenario, minus_create_task, minus_submit_task
from cortexlab_remote import cortexlab_Remote
from reservation_registry import get_all_reservation, get_reservation, update_reservation
from job_runner import run_job
import threading
import json
import os
import re


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
        #start threading for monitoring reservation.
        threading.Thread(target=reservation_monitor, args=(job_id,), daemon=True).start()
    
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
    
    if reservation is None:
        return jsonify({
            "success": False,
            "message": f"Reservation {job_id} not found or has already finished."
        }),     404

    print("Reservation:", reservation)

    
    
    task_description = data.get("task_description", "")
    safe_desc = re.sub(r'[^a-zA-Z0-9_-]', '_', task_description.strip())
    local_folder = os.path.join(str(job_id), safe_desc)
    remote_folder = f"{job_id}/{safe_desc}"
    
    nodes = reservation["assigned_nodes"]  
    duration = walltime_to_seconds(reservation["walltime"])
    

    generate_scenario(local_folder, nodes, duration, task_description)
    remote = cortexlab_Remote()
    
    remote.upload_folder(local_folder, remote_folder)
    minus_create_task(remote, remote_folder)
    task_id = minus_submit_task(remote, remote_folder)

    #starting thread for monitor task.
    threading.Thread(target=minus_task_monitor, args=(job_id, task_id), daemon=True).start()

    task_entry = {
        "task_id": task_id,
        "description": task_description,
        "state": "SUBMITTED",
        "folder": remote_folder
    }

    reservation["tasks"].append(task_entry)

    update_reservation(job_id=job_id, tasks=reservation["tasks"])



    return jsonify({
        "success": True,
        "task_id": task_id
    })

@app.route("/status/task")
def status_task(job_id, task_id):
    data = get_reservation(job_id)
    status = data["task_status"]
    return jsonify({
        "success": True,
        "task_status": status
    })

node_monitor_thread = None
@app.route("/status/nodes")
def status_nodes():
    #Node state monitor thread
    global node_monitor_thread
    reservations = get_all_reservation()
    start_monitor = False
    for reservation in reservations.values():

        for task in reservation.get("tasks", []):

            if task["state"] == "RUNNING":
                nodes = reservation["assigned_nodes"]
                start_monitor = True
                break
    if start_monitor:
        if node_monitor_thread is None or not node_monitor_thread.is_alive():
            node_monitor_thread = threading.Thread(target=monitor_nodes, args=(nodes, 5), daemon=True)
            node_monitor_thread.start()
            print("node monitor started().") 
                
    return jsonify(get_nodes())

@app.route("/script/upload", methods=["POST"])
def upload_script():

    node = request.form["node"]
    file = request.files["script"]
    update_job(node=node, script = file.filename)

    os.makedirs("uploads", exist_ok=True)

    local_path = os.path.join("uploads", file.filename)
    file.save(local_path)

    node_data = get_node(node)

    job = node_data["job"]
    task_folder = job["folder"]

    remote_folder = f"{task_folder}/{node}"
    
    remote = cortexlab_Remote()

    remote.upload_folder(local_path, remote_folder)
    remote.close()

    remote_path = f"{remote_folder}/{file.filename}"


    remote.close()

    return jsonify({
        "success": True,
        "message": "Upload Successful",
        "remote_path": remote_path
    })

@app.route("/control/job/start", methods = ["POST"])
def start_job():
    data = request.get_json()
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


