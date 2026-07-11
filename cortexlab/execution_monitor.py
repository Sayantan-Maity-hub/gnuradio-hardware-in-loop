import threading
import re
import config
from ssh_client import SSHConnection
from execution_registy import(get_execution, update_execution)
from node_registry import get_node

def execute_script(execution_id):
    execution = get_execution(execution_id)
    
    if execution is None:
        return
    
    node = execution["node"]
    folder = execution["folder"]
    script = execution["script"]
    runner = execution["runner"]

    node_info = get_node(node)

    if node_info is None:
        update_execution(execution_id, stderr="Assigned node not found")
        return
    if node_info["status"] != "ONLINE":
        update_execution(execution_id, stderr="Assigned node is not ONLINE")
    
    update_execution(execution_id, state = "ASSIGNED")


    ssh = SSHConnection(node)
    try :
        update_execution(execution_id, state = "PREPARING")
        update_execution("PREARING")
        remote_script = f"/cortexlab/homes/{config.USERNAME}/{folder}/{script}"
        print(remote_script)
        log_path = f"/cortexlab/homes/{config.USERNAME}/{folder}/execution_{execution_id}.log"

        stdout, stderr = ssh.run_on_node(f'test -f "{remote_script}" && echo OK')
        exist = stdout.read().decode().strip()
        print(exist)

        if exist != "OK":
            update_execution(execution_id, error="Experiment script not found on remote server.")

        update_execution(execution_id, state = "READY")

        cmd = f"{runner} {remote_script}"
        print (cmd)

        run_cmd = (
            f"{cmd} 2>&1 | tee {log_path}"

        )
        stdout, stderr = ssh.run_on_node(run_cmd)
        update_execution(execution_id, state = "RUNNING")
        print(stdout)
        output = stdout.read().decode()
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line, end="")
            output += line
            update_execution(execution_id, stdout = output)
        error = stderr.read().decode()
        if error:
            update_execution(execution_id, stderr=error)
        exit_code = stdout.channel.recv_exit_status()
        result = "UNKWON"
        match = re.search(r"::STATUS:.*:(PASS|FAIL):", output)
        if match:
            result = match.group(1)
        elif exit_code == 0:
            result = "SUCCESS"
        else:
            result = "FAILED"

        update_execution(execution_id=execution_id, state = "FINISHED", exit_code = exit_code)

        
    except Exception as e:
        update_execution(execution_id, error=str(e))
    finally:
        ssh.close()
