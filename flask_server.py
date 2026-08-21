from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from cortexlab.reservation.reservation_task_creation import create_task_for_reservation
from cortexlab.nodes.node_registry import get_nodes, wait_for_node_status
from cortexlab.reservation.reservation import reserve_nodes
from cortexlab.reservation.reservation_monitor import reservation_monitor
from cortexlab.reservation.reservation_registry import (
    get_all_reservation,
    get_reservation,
)

from experiment_manager.generic_experiment_runner import run_generic_experiment
from cortexlab.execution.execution_registy import get_execution, get_all_execution

import threading
import logging
import traceback

app = Flask(__name__)

CORS(app)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


global current_reservation_job_id


@app.route("/run-experiment", methods=["POST"])
def create_experiment():
    global current_reservation_job_id

    current_reservation_job_id = None

    data = request.get_json(silent=True) or {}

    try:
        pr_id = data["pr_id"]
        experiment_name = data["experiment"]

        # Check if an active reservation already exists
        reservation = None

        if current_reservation_job_id is not None:
            reservation = get_reservation(current_reservation_job_id)

            # Reservation finished/expired
            if reservation is not None:

                state = reservation.get("state", "").lower()

                if state not in ["submitted", "waiting", "running"]:
                    reservation = None
                    current_reservation_job_id = None

        # Create reservation only if none exists
        if reservation is None:

            print("No active reservation found.")
            print("Creating new reservation...")

            job_id = reserve_nodes(
                hostname=data["hostname"],
                username=data["username"],
                walltime=data["walltime"],
                reservation_name=data["reservation_name"],
            )

            current_reservation_job_id = job_id

            # Start reservation monitor
            threading.Thread(
                target=reservation_monitor, args=(job_id,), daemon=True
            ).start()

            # Create task only once
            task_id = create_task_for_reservation(job_id)

            print(f"Created reservation {job_id} and task {task_id}")

        else:

            # Reuse existing reservation
            job_id = reservation["job_id"]

            print(f"Using existing reservation {job_id}")

            tasks = reservation.get("tasks", [])

            if not tasks:
                task_id = create_task_for_reservation(job_id)
            else:
                task_id = tasks[0]["task_id"]

            print(f"Using existing task {task_id}")

        reservation = get_reservation(job_id)

        if reservation is None:
            raise RuntimeError(f"Reservation {job_id} not found")

        # Wait until reservation monitor has populated the status of all assigned nodes.
        try:
            node_status = wait_for_node_status(job_id, timeout=300)

            print(f"Nodes are ready for experiment: {node_status}")

        except TimeoutError as e:

            return {
                "success": False,
                "error": str(e),
                "retry_allowed": True,
            }, 503

        # Run selected experiment
        parameter = data["parameter"]

        result = run_generic_experiment(
            experiment_name=experiment_name,
            job_id=job_id,
            pr_id=pr_id,
            parameter=parameter,
        )

        return (
            jsonify(
                {
                    "success": True,
                    "job_id": job_id,
                    "pr_id": pr_id,
                    "experiment": experiment_name,
                    "result": result,
                }
            ),
            200,
        )

    except Exception as e:

        print(f"Experiment request failed: {e}")
        traceback.print_exc()

        return jsonify({"success": False, "retry_allowed": True, "error": str(e)}), 400


""" ----------Api to get the status of a reservation by job_id----------"""


@app.route("/status/reservations/<int:job_id>", methods=["GET"])
def reservation_status_by_id(job_id):
    reservation = get_reservation(job_id)

    if reservation is None:
        return (
            jsonify({"success": False, "message": f"Reservation {job_id} not found"}),
            404,
        )

    return jsonify({"success": True, "reservation": reservation}), 200


@app.route("/status/reservations", methods=["GET"])
def reservation_statuses():
    """Return every reservation currently tracked by the controller."""
    reservations = get_all_reservation()
    return (
        jsonify(
            {
                "success": True,
                "count": len(reservations),
                "data": reservations,
            }
        ),
        200,
    )


"""----------Api to get the status of all nodes----------"""


@app.route("/status/nodes", methods=["GET"])
def node_status():
    nodes_status = get_nodes()
    return (
        jsonify({"success": True, "count": len(nodes_status), "data": nodes_status}),
        200,
    )


"""-------------Api to get execution status--------------"""


@app.route("/status/experiment/<experiment_id>", methods=["GET"])
def exeperiment_status(experiment_id):
    experiment = get_execution(experiment_id)
    if experiment is None:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Experiment {experiment_id} not found",
                }
            ),
            404,
        )
    return jsonify({"success": True, "experiment": experiment}), 200


@app.route("/status/experiments", methods=["GET"])
def experiment_statuses():
    """Return every experiment currently tracked by the controller."""
    experiments = get_all_execution()
    return (
        jsonify(
            {
                "success": True,
                "count": len(experiments),
                "data": experiments,
            }
        ),
        200,
    )


def start_flask():
    log = logging.getLogger("werkzeug")
    log.disabled = True
    app.run(host="0.0.0.0", port=5678, debug=False, use_reloader=False)
