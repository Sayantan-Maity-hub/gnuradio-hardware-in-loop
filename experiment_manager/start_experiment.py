import threading
import time

from  cortexlab.execution.execute_node_script import execute_script
from cortexlab.execution.execution_registy import update_execution, get_execution


def start_experiment(experiment_id, job_id):

    experiment = get_execution(experiment_id)

    if experiment is None:
        raise RuntimeError(
            f"Experiment {experiment_id} not found"
        )

    nodes = experiment.get("nodes", {})

    if not nodes:

        raise RuntimeError(f"No nodes configured for experiment {experiment_id}")

    ready_barrier = threading.Barrier(len(nodes))

    start_at = time.time() + 2

    threads = []

    for node, node_info in nodes.items():

        script = node_info.get("script")

        if not script:

            raise RuntimeError(f"No script configured for node {node}")

        thread = threading.Thread(target=execute_script, args=(experiment_id, node, script,),
            kwargs={"ready_barrier": ready_barrier, "start_at": start_at,}, daemon=True,)

        thread.start()
        threads.append(thread)

    return {
        "success": True,
        "experiment_id": experiment_id,
        "job_id": job_id,
        "nodes": list(nodes.keys()),
        "state": "STARTING",
    }