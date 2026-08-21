import json
import re
import shlex
import threading
import time

from cortexlab.execution.execution_registy import (get_execution, update_execution, update_execution_node,)

from cortexlab.nodes.node_registry import get_node
from .execute_analysis import execute_analysis

from ..remote_connections.ssh_connection import SSHConnection


RESULT_PREFIX = "::RESULT::"


def _extract_experiment_result(output): 

    result = None

    for line in output.splitlines():

        if not line.startswith(RESULT_PREFIX):
            continue

        payload = line[len(RESULT_PREFIX):].strip()

        try:
            parsed = json.loads(payload)

        except json.JSONDecodeError as error:
            return (None, f"Invalid experiment result JSON: {error.msg}")

        if not isinstance(parsed, dict):
            return (None, "Experiment result must be a JSON object")

        if parsed.get("status") not in {"passed", "failed"}:
            return (None, 'Experiment result status must be ''"passed" or "failed"')

        if "metrics" not in parsed:
            parsed["metrics"] = {}

        if not isinstance(parsed["metrics"], dict):
            return (None, "Experiment result metrics must be a JSON object")

        result = parsed

    return result, None


''' Check whether all primary experiment nodes are finished. start analysis . 
execute_analysis() will download result.json produce by analysis script.
if any primary node fails experiment become failed'''
    
def finish_experiment_if_complete(experiment_id):
    

    experiment = get_execution(experiment_id)

    if experiment is None:
        return

    nodes = experiment.get("nodes", {})

    if not nodes:
        return

    node_executions = list(nodes.values())

    # Already finished / analysis already running
    if experiment.get("state") in {"ANALYSIS_RUNNING", "FINISHED", "FAILED"}:
        return

    # Check whether any primary node failed
    if any(node.get("state") == "FAILED" for node in node_executions):

        update_execution(
            experiment_id,
            state="FAILED",
            overall_result="FAILED",
            ended=time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

        return

    # Wait until ALL primary nodes finish
    while True:
        if not all( node.get("state") == "FINISHED" for node in node_executions):
            continue

        # Check primary node results
        passed = all( node.get("result") in { "PASS", "SUCCESS"} for node in node_executions)

        if not passed:

            update_execution(
                experiment_id,
                state="FAILED",
                overall_result="FAILED",
                ended=time.strftime("%Y-%m-%d %H:%M:%S")
            )

        # TX/RX successfully finished
        print( f"Experiment {experiment_id}: TX/RX finished successfully.")

        #Execute analysis script
        update_execution(experiment_id, state="NODE_EXECUTION_FINISHED", overall_result=passed)

        return passed



# FAIL EXPERIMENT
def _fail_execution(experiment_id, message, ready_barrier=None, failed_node=None):
    
    execution = get_execution(experiment_id)

    if execution is None:
        return

    # Mark failed node
    if failed_node is not None:

        update_execution_node(
            experiment_id,
            failed_node,
            state="FAILED",
            result="FAILED",
            stderr=message,
            ended=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    # Mark experiment failed

    update_execution(
        experiment_id,
        state="FAILED",
        overall_result="FAILED",
        stderr=message,
        ended=time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

    # Break synchronization barrier

    if ready_barrier is not None:

        try:
            ready_barrier.abort()

        except threading.BrokenBarrierError:
            pass