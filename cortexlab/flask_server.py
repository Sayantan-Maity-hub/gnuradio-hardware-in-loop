from flask import Flask, Response, render_template, request, jsonify
from flask_cors import CORS
from node_registry import get_nodes, get_node, update_job
from reservation import reserve_nodes, walltime_to_seconds
from reservation_monitor import reservation_monitor
from minus_task_monitor import minus_task_monitor
from monitor_nodes import monitor_nodes
from scenario_generator import generate_scenario, minus_create_task, minus_submit_task
from cortexlab_remote import cortexlab_Remote
from reservation_registry import (
    get_all_reservation,
    get_reservation,
    update_reservation,
)
from execution_monitor import execute_script
from execution_registy import (
    create_execution,
    update_execution,
    get_execution,
    get_all_execution,
)
from execution_group_registry import (
    create_execution_group,
    get_execution_group,
    get_all_execution_groups,
    add_node_execution,
    update_execution_group,
    get_active_node_conflicts,
)
from script_parser import script_parser
import threading
from config import USERNAME, HOSTNAME
import json
import os
import re
import logging
import time

app = Flask(__name__)

CORS(app)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/reservation/create", methods=["POST"])
def create_reserve():
    data = request.get_json()
    try:
        job_id = reserve_nodes(
            hostname=data["hostname"],
            username=data["username"],
            reservation_type=data["reservation_type"],
            walltime=data["walltime"],
            future=data["future"],
            reservation_time=data.get("reservatoion_time"),
            preferred_nodes=data.get("preferred_nodes", []),
        )
        # start threading for monitoring reservation.
        threading.Thread(
            target=reservation_monitor, args=(job_id,), daemon=True
        ).start()

        return jsonify({"job_id": job_id})
    except Exception as e:
        return jsonify({"success": False, "retry_allowed": True, "error": str(e)}), 400


@app.route("/status/reservations")
def reservation_status():
    return jsonify(list(get_all_reservation().values()))


@app.route("/task/create", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No requese data received"}), 400
    job_id = int(data.get("job_id"))
    if not job_id:
        return jsonify({"success": False, "message": "job_id missing"})

    reservation = get_reservation(job_id)

    if reservation is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Reservation {job_id} not found or has already finished.",
                }
            ),
            404,
        )

    print("Reservation:", reservation)

    task_description = data.get("task_description", "")
    safe_desc = re.sub(r"[^a-zA-Z0-9_-]", "_", task_description.strip())
    local_folder = os.path.join(str(job_id), safe_desc)
    remote_folder = f"{job_id}/{safe_desc}"

    nodes = reservation["assigned_nodes"]
    duration = walltime_to_seconds(reservation["walltime"])

    generate_scenario(local_folder, nodes, duration, task_description)
    remote = cortexlab_Remote()

    remote.upload_folder(local_folder, remote_folder)
    minus_create_task(remote_folder)
    task_entry = {
            "task_id": None,
            "description": task_description,
            "state": "SUBMITTED",
            "folder": remote_folder,
        }
    
    reservation["tasks"].append(task_entry)
    
    update_reservation(job_id=job_id, tasks=reservation["tasks"])

    threading.Thread(
        target=minus_submit_task, args=(job_id, remote_folder), daemon=True
    ).start()

    return jsonify({
    "success": True,
    "message": "Task queued successfully."
    })


@app.route("/status/task")
def status_task(job_id):
    data = get_reservation(job_id)
    status = data["task_status"]
    return jsonify({"success": True, "task_status": status})


node_monitor_thread = None


@app.route("/status/nodes")
def status_nodes():
    # Node state monitor thread
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
            node_monitor_thread = threading.Thread(
                target=monitor_nodes, args=(nodes, 5), daemon=True
            )
            node_monitor_thread.start()
            print("node monitor started().")

    return jsonify(get_nodes())


@app.route("/script/upload", methods=["POST"])
def upload_script():

    node = request.form["node"]
    file = request.files["script"]
    group_id_value = request.form.get("group_id")
    group = None

    if group_id_value is not None:
        try:
            group_id = int(group_id_value)
        except ValueError:
            return jsonify({"success": False, "message": "group_id must be an integer"}), 400

        group = get_execution_group(group_id)
        if group is None:
            return jsonify({"success": False, "message": "Execution group not found"}), 404
        if node not in group["nodes"]:
            return jsonify({
                "success": False,
                "message": "This node is not part of the execution group",
            }), 400

    update_job(node=node, script=file.filename)

    os.makedirs("uploads", exist_ok=True)

    local_path = os.path.join("uploads", file.filename)
    file.save(local_path)

    node_data = get_node(node)

    job = node_data["job"]
    task_folder = group["folder"] if group else job["folder"]

    remote_folder = f"{task_folder}/{node}"


    script_name = os.path.basename(local_path)
    execution_id = create_execution(
        job_id=group["job_id"] if group else job.get("job_id"),
        task_id=group["task_id"] if group else job.get("task_id"),
        node=node,
        folder=remote_folder,
        script=script_name,
        runner=None,
        group_id=group["group_id"] if group else None,
    )

    update_job(node=node, execution_id=execution_id)

    remote = cortexlab_Remote()

    remote.upload_folder(local_path, remote_folder)
    remote.close()

    remote_path = f"{remote_folder}/{script_name}"
    update_execution(execution_id, state="CREATED", script=script_name)

    if group:
        add_node_execution(group["group_id"], node, execution_id)
        refreshed_group = get_execution_group(group["group_id"])
        if set(refreshed_group["execution_ids"]) == set(refreshed_group["nodes"]):
            update_execution_group(
                group["group_id"],
                state="READY_TO_RUN",
                sync_state="ALL_SCRIPTS_UPLOADED",
            )
        else:
            update_execution_group(
                group["group_id"],
                state="UPLOADING",
                sync_state="WAITING_FOR_UPLOADS",
            )

    return jsonify(
        {
            "success": True,
            "message": "Upload Successful",
            "remote_path": remote_path,
            "execution_id": execution_id,
            "group_id": group["group_id"] if group else None,
        }
    )


@app.route("/script/run", methods=["POST"])
def run_script():
    data = request.get_json()

    node = data.get("node")
    node_data = get_node(node)

    if node_data is None:
        return jsonify({"success": False, "message": "Node not found"}), 400
    job = node_data.get("job", {})
    task_folder = job.get("folder")
    script = job.get("script")
    execution_id = job.get("execution_id")

    if not script:
        return jsonify({"success": False, "message": "No script uploaded"}), 400
    

    threading.Thread(target=execute_script, args=(execution_id,), daemon=True).start()

    return (
        jsonify(
            {
                "success": True,
                "execution_id": execution_id,
                "message": "Execution started",
            }
        ),
        200,
    )


@app.route("/status/execution")
def status_execution():
    executions = get_all_execution()

    return jsonify({"success": True, "count": len(executions), "data": executions}), 200


@app.route("/execution-groups", methods=["POST"])
def create_execution_group_route():
    
    data = request.get_json(silent=True) or {}
    job_id = data.get("job_id")
    task_id = data.get("task_id")
    name = (data.get("name") or "Unnamed execution group").strip()
    nodes = data.get("nodes") or []

    if job_id is None or task_id is None or not isinstance(nodes, list) or not nodes:
        return jsonify({
            "success": False,
            "message": "job_id, task_id, and a non-empty nodes list are required",
        }), 400

    if len(nodes) != len(set(nodes)):
        return jsonify({"success": False, "message": "A node can appear only once"}), 400

    reservation = get_reservation(int(job_id))
    if reservation is None:
        return jsonify({"success": False, "message": "Reservation not found"}), 404

    if not set(nodes).issubset(set(reservation.get("assigned_nodes", []))):
        return jsonify({
            "success": False,
            "message": "Every selected node must belong to this reservation",
        }), 400

    conflicts = get_active_node_conflicts(nodes)
    if conflicts:
        return jsonify({
            "success": False,
            "message": "One or more selected nodes are already allocated to an active execution group",
            "conflicting_group_ids": conflicts,
        }), 409

    task = next(
        (item for item in reservation.get("tasks", [])
         if str(item.get("task_id")) == str(task_id)),
        None,
    )
    if task is None:
        return jsonify({"success": False, "message": "Task not found in reservation"}), 404

    group_id = create_execution_group(
        job_id=int(job_id),
        task_id=int(task_id),
        name=name,
        nodes=nodes,
        folder=task.get("folder"),
    )
    return jsonify({"success": True, "group_id": group_id}), 201


@app.route("/execution-groups", methods=["GET"])
def status_execution_groups():
    groups = get_all_execution_groups()
    return jsonify({"success": True, "count": len(groups), "data": groups}), 200


@app.route("/execution-groups/<int:group_id>/run", methods=["POST"])
def run_execution_group(group_id):
    """Prepare every group node, wait until all are ready, then run together."""
    group = get_execution_group(group_id)
    if group is None:
        return jsonify({"success": False, "message": "Execution group not found"}), 404

    if group["state"] in {"RUNNING", "FINISHED", "FAILED", "CANCELLED"}:
        return jsonify({
            "success": False,
            "message": f"Execution group cannot run while state is {group['state']}",
        }), 409

    expected_nodes = set(group["nodes"])
    uploaded_nodes = set(group["execution_ids"])
    if uploaded_nodes != expected_nodes:
        missing = sorted(expected_nodes - uploaded_nodes)
        return jsonify({
            "success": False,
            "message": "Upload one script for every group node",
            "missing_nodes": missing,
        }), 400

    offline_nodes = [
        node for node in group["nodes"]
        if not get_node(node) or get_node(node).get("status") != "ONLINE"
    ]
    if offline_nodes:
        return jsonify({
            "success": False,
            "message": "Every group node must be ONLINE before running",
            "offline_nodes": offline_nodes,
        }), 409

    barrier = threading.Barrier(len(group["nodes"]))
    start_at = time.time() + 3
    update_execution_group(
        group_id,
        state="PREPARING",
        sync_state="WAITING_FOR_NODES",
        result=None,
        error=None,
        started_at=None,
        finished_at=None,
    )

    for execution_id in group["execution_ids"].values():
        threading.Thread(
            target=execute_script,
            args=(execution_id, barrier, start_at),
            daemon=True,
        ).start()

    return jsonify({
        "success": True,
        "group_id": group_id,
        "message": "Preparing all nodes; scripts start when every node is READY",
    }), 202


@app.route("/status/job/<node>")
def job_status(node):
    node_data = get_node(node)
    if not node_data:
        return {"error": "node not found"}, 404
    return node_data.get("job", {})


def start_flask():
    log = logging.getLogger("werkzeug")
    log.disabled = False
    app.run(host="0.0.0.0", port=5678, debug=True, use_reloader=False)
