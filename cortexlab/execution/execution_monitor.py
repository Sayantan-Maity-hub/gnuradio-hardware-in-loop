import json
import re
import shlex
import threading
import time

import config

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
    if not all( node.get("state") == "FINISHED" for node in node_executions):
        return

    # Check primary node results
    passed = all( node.get("result") in { "PASS", "SUCCESS"} for node in node_executions)

    if not passed:

        update_execution(
            experiment_id,
            state="FAILED",
            overall_result="FAILED",
            ended=time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

        return

    # TX/RX successfully finished
    print( f"Experiment {experiment_id}: TX/RX finished successfully.")

    # Start analysis
    analysis_script = experiment.get( "analysis_script")
    folder = experiment.get("folder")

    if analysis_script and folder:

        print(
            f"Starting analysis for experiment {experiment_id}")

        update_execution(
            experiment_id,
            state="ANALYSIS_RUNNING",
            overall_result=None,
        )

        analysis_thread = threading.Thread(target=execute_analysis, args=(experiment_id, analysis_script), daemon=True,)
        analysis_thread.start()

        return
    # No analysis configured
    update_execution(
        experiment_id,
        state="FINISHED",
        overall_result="PASS",
        ended=time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

# FAIL EXPERIMENT
def _fail_execution(experiment_id, message, ready_barrier=None, failed_node=None):
    
    execution = get_execution(
        experiment_id
    )

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
            ended=time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
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


"""
    Prepare and execute one primary experiment node. Both nodes become READY first and then start
    at approximately the same time.
    """
def execute_script( experiment_id, node, script, ready_barrier=None, start_at=None,):
    
    experiment = get_execution(
        experiment_id
    )

    if experiment is None:
        return

    folder = experiment["folder"]

    ssh = None

    try:
        # Check node
        node_info = get_node(node)

        if node_info is None:

            _fail_execution(
                experiment_id,
                f"Assigned node {node} not found",
                ready_barrier,
                node,
            )

            return

        if node_info.get("status") != "ONLINE":

            _fail_execution(
                experiment_id,
                f"Assigned node {node} is not ONLINE",
                ready_barrier,
                node,
            )

            return

        # PREPARING
        update_execution_node(
            experiment_id,
            node,
            state="PREPARING",
        )

        # SSH
        ssh = SSHConnection(node)

        remote_dir = (
            f"/cortexlab/homes/"
            f"{config.USERNAME}/"
            f"{folder}"
        )

        remote_script = (f"{remote_dir}/{node}/{script}")

        log_path = (f"{remote_dir}/{node}/execution_{experiment_id}.log")

        update_execution_node(
            experiment_id,
            node,
            log_path=log_path,
        )

        # Check script
        stdout, _ = ssh.run_on_node(
            f'test -f '
            f'{shlex.quote(remote_script)} '
            f'&& echo OK'
        )

        if stdout.read().decode().strip() != "OK":

            _fail_execution(
                experiment_id,
                (
                    f"Script not found for {node}: "
                    f"{remote_script}"
                ),
                ready_barrier,
                node,
            )

            return

        # chmod
        chmod_stdout, chmod_stderr = (
            ssh.run_on_node(f"chmod +x {shlex.quote(remote_script)}"))

        chmod_exit = (chmod_stdout.channel.recv_exit_status())

        if chmod_exit != 0:

            _fail_execution(
                experiment_id,
                (
                    f"Could not make script executable "
                    f"on {node}: "
                    f"{chmod_stderr.read().decode().strip()}"
                ),
                ready_barrier,
                node,
            )

            return

        # READY
        update_execution_node(
            experiment_id,
            node,
            state="READY",
        )

        print(f"{experiment_id}: {node} READY")

        # WAIT FOR ALL NODES
        if ready_barrier is not None:

            try:
                ready_barrier.wait(timeout=60)

            except threading.BrokenBarrierError:

                _fail_execution(experiment_id, ("Synchronization failed: a node did not become READY within 60 seconds"))
                return

        # COMMON START TIME
        if start_at is not None:

            delay = start_at - time.time()

            if delay > 0:
                time.sleep(delay)

        # RUNNING
        started_at = time.strftime("%Y-%m-%d %H:%M:%S")

        update_execution_node(
            experiment_id,
            node,
            state="RUNNING",
            execution_started_at=started_at,
        )

        print(f"{experiment_id}: {node} RUNNING")

        # Execute script
        pipeline = (
            f"source {shlex.quote(config.TOOLCHAIN_ENV)} && "
            f"cd {shlex.quote(remote_dir)} && "
            f"{shlex.quote(remote_script)} "
            f"2>&1 | tee {shlex.quote(log_path)}"
        )

        stdout, stderr = ssh.run_on_node(f"bash -o pipefail -c {shlex.quote(pipeline)}")

        # Read output
        output_parts = []

        while True:
            line = stdout.readline()
            if not line:
                break

            output_parts.append(line)

            update_execution_node(
                experiment_id,
                node,
                stdout="".join(output_parts),
            )

        error = stderr.read().decode()

        output = "".join(output_parts)

        exit_code = (stdout.channel.recv_exit_status())

        # Parse log result
        experiment_result, result_error = (_extract_experiment_result(output))

        # Legacy STATUS parser

        match = re.search(r"::STATUS:.*:(PASS|FAIL):", output)

        # Determine result
        if exit_code != 0:

            result = "FAILED"
            state = "FAILED"

        elif result_error:

            result = "FAILED"
            state = "FAILED"

            error = (
                f"{error}\n"
                f"{result_error}"
            ).strip()

        elif experiment_result is not None:

            result = (
                "PASS"
                if experiment_result["status"]
                == "passed"
                else "FAIL"
            )

            state = (
                "FINISHED"
                if result == "PASS"
                else "FAILED"
            )

        else:

            result = (
                match.group(1)
                if match
                else "SUCCESS"
            )

            state = (
                "FINISHED"
                if result != "FAIL"
                else "FAILED"
            )

        # Update node result

        update_execution_node(
            experiment_id,
            node,
            state=state,
            result=result,
            experiment_result=experiment_result,
            stdout=output,
            stderr=error,
            exit_code=exit_code,
            ended=time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

        print(
            f"{experiment_id}: {node} -> {result}")

        # Check whether all nodes finished
        finish_experiment_if_complete(experiment_id)

    except Exception as error:

        _fail_execution(
            experiment_id,
            str(error),
            ready_barrier,
            node,
        )

    finally:

        if ssh is not None:
            ssh.close()