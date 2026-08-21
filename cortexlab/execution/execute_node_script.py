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
from .execution_monitor import _fail_execution, _extract_experiment_result

RESULT_PREFIX = "::RESULT::"


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

        error = stderr.read().decode()

        output = stdout.read().decode()

        exit_code = (stdout.channel.recv_exit_status())


        # Determine result
        if exit_code == 0:

            result = "SUCCESS"
            state = "FINISHED"
        else:
            result = "FAILED"
            state = "FAILED"

        # Update node result

        update_execution_node(
            experiment_id,
            node,
            state=state,
            result=result,
            stdout=output,
            stderr=error,
            exit_code=exit_code,
            ended=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        print(f"{experiment_id}: {node} -> {result}")

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