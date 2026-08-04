import json
import re
import shlex
import threading
import time

import config
from execution_group_registry import get_execution_group, update_execution_group
from execution_registy import get_execution, update_execution
from node_registry import get_node
from ssh_client import SSHConnection


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
            return None, f"Invalid experiment result JSON: {error.msg}"
        if not isinstance(parsed, dict):
            return None, "Experiment result must be a JSON object"
        if parsed.get("status") not in {"passed", "failed"}:
            return None, 'Experiment result status must be "passed" or "failed"'
        if "metrics" not in parsed:
            parsed["metrics"] = {}
        if not isinstance(parsed["metrics"], dict):
            return None, "Experiment result metrics must be a JSON object"
        result = parsed
    return result, None


def _finish_group_if_complete(group_id):

    if group_id is None:
        return

    group = get_execution_group(group_id)
    if group is None or not group["execution_ids"]:
        return

    executions = [
        get_execution(execution_id)
        for execution_id in group["execution_ids"].values()
    ]
    if any(execution is None for execution in executions):
        update_execution_group(
            group_id,
            state="FAILED",
            sync_state="FAILED",
            result="FAILED",
            finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return

    if any(execution["state"] == "FAILED" for execution in executions):
        update_execution_group(
            group_id,
            state="FAILED",
            sync_state="FAILED",
            result="FAILED",
            finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        return

    if all(execution["state"] == "FINISHED" for execution in executions):
        passed = all(execution.get("result") in {"PASS", "SUCCESS"} for execution in executions)
        update_execution_group(
            group_id,
            state="FINISHED" if passed else "FAILED",
            sync_state="COMPLETE" if passed else "FAILED",
            result="PASS" if passed else "FAILED",
            finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )


def _fail_execution(execution_id, message, ready_barrier=None):
    execution = get_execution(execution_id)
    group_id = execution.get("group_id") if execution else None
    update_execution(
        execution_id,
        state="FAILED",
        result="FAILED",
        stderr=message,
        ended=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    if ready_barrier is not None:
        try:
            ready_barrier.abort()
        except threading.BrokenBarrierError:
            pass
    if group_id is not None:
        update_execution_group(
            group_id,
            state="FAILED",
            sync_state="FAILED",
            result="FAILED",
            error=message,
            finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )


def execute_script(execution_id, ready_barrier=None, start_at=None):
    """Prepare one node script and, when provided, synchronize it with its group."""
    execution = get_execution(execution_id)
    if execution is None:
        return

    node = execution["node"]
    folder = execution["folder"]
    script = execution["script"]
    group_id = execution.get("group_id")
    ssh = None

    try:
        node_info = get_node(node)
        if node_info is None:
            _fail_execution(execution_id, "Assigned node not found", ready_barrier)
            return
        if node_info.get("status") != "ONLINE":
            _fail_execution(execution_id, "Assigned node is not ONLINE", ready_barrier)
            return

        update_execution(execution_id, state="PREPARING")
        ssh = SSHConnection(node)
        remote_script = f"/cortexlab/homes/{config.USERNAME}/{folder}/{script}"
        log_path = f"/cortexlab/homes/{config.USERNAME}/{folder}/execution_{execution_id}.log"

        stdout, _ = ssh.run_on_node(f'test -f {shlex.quote(remote_script)} && echo OK')
        if stdout.read().decode().strip() != "OK":
            _fail_execution(execution_id, "Experiment script not found on remote server", ready_barrier)
            return

        chmod_stdout, chmod_stderr = ssh.run_on_node(f"chmod +x {shlex.quote(remote_script)}")
        chmod_exit = chmod_stdout.channel.recv_exit_status()
        if chmod_exit != 0:
            _fail_execution(
                execution_id,
                f"Could not make script executable: {chmod_stderr.read().decode().strip()}",
                ready_barrier,
            )
            return

        update_execution(execution_id, state="READY")
        if group_id is not None:
            update_execution_group(group_id, sync_state="WAITING_FOR_NODES")

        if ready_barrier is not None:
            try:
                ready_barrier.wait(timeout=60)
            except threading.BrokenBarrierError:
                _fail_execution(
                    execution_id,
                    "Synchronization failed: a group node did not become ready in 60 seconds",
                )
                return

        if start_at is not None:
            delay = start_at - time.time()
            if delay > 0:
                time.sleep(delay)

        update_execution(execution_id, state="RUNNING")
        if group_id is not None:
            update_execution_group(
                group_id,
                state="RUNNING",
                sync_state="RUNNING",
                started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            )


        pipeline = f"{shlex.quote(remote_script)} 2>&1 | tee {shlex.quote(log_path)}"
        run_cmd = f"bash -o pipefail -c {shlex.quote(pipeline)}"
        stdout, stderr = ssh.run_on_node(run_cmd)
        output_parts = []
        while True:
            line = stdout.readline()
            if not line:
                break
            output_parts.append(line)
            update_execution(execution_id, stdout="".join(output_parts))

        error = stderr.read().decode()
        output = "".join(output_parts)
        exit_code = stdout.channel.recv_exit_status()
        experiment_result, result_error = _extract_experiment_result(output)

        match = re.search(r"::STATUS:.*:(PASS|FAIL):", output)
        if exit_code != 0:
            result = "FAILED"
            state = "FAILED"
        elif result_error:
            result = "FAILED"
            state = "FAILED"
            error = f"{error}\n{result_error}".strip()
        elif experiment_result is not None:
            result = "PASS" if experiment_result["status"] == "passed" else "FAIL"
            state = "FINISHED" if result == "PASS" else "FAILED"
        else:
            result = match.group(1) if match else "SUCCESS"
            state = "FINISHED" if result != "FAIL" else "FAILED"
        update_execution(
            execution_id,
            state=state,
            result=result,
            experiment_result=experiment_result,
            stdout=output,
            stderr=error,
            exit_code=exit_code,
            ended=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    except Exception as error:
        _fail_execution(execution_id, str(error), ready_barrier)
    finally:
        if ssh is not None:
            ssh.close()
        _finish_group_if_complete(group_id)
