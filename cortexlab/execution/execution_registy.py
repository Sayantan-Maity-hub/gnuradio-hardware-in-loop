import threading
import time

execution_registry = {}
lock = threading.Lock()


def create_experiment_registry(
    experiment_id,
    experiment_name,
    nodes,
    analysis_script=None,
    folder=None,
):
    with lock:

        # Do NOT overwrite the input `nodes`
        node_registry = {}

        for node_name, script in nodes.items():

            node_registry[node_name] = {
                "script": script,
                "state": "STARTING",
                "stdout": "",
                "stderr": "",
                "result": None,
                "experiment_result": None,
                "log_path": None,
                "execution_started_at": None,
                "started": None,
                "ended": None,
            }

        execution_registry[experiment_id] = {
            "experiment_name": experiment_name,
            "nodes": node_registry,
            "analysis_script": analysis_script,
            "folder": folder,
            "state": "STARTING",
            "overall_result": None,
            "experiment_result": None,
            "stdout": "",
            "stderr": "",
            "log_path": None,
            "execution_started_at": None,
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ended": None,
        }


def update_execution(execution_id, **kwargs):
    with lock:

        if execution_id not in execution_registry:
            return False

        execution_registry[execution_id].update(kwargs)

        return True


def update_execution_node(experiment_id, node, **kwargs):
    with lock:

        experiment = execution_registry.get(experiment_id)

        if experiment is None:
            return False

        nodes = experiment.get("nodes", {})

        if node not in nodes:
            return False

        nodes[node].update(kwargs)

        return True


def clear_execution(experiment_id):

    with lock:

        if experiment_id in execution_registry:
            del execution_registry[experiment_id]


def get_execution(experiment_id):

    with lock:

        return execution_registry.get(experiment_id)


def get_all_execution():

    with lock:

        return dict(execution_registry)
