import threading
import re
import config
from ssh_client import SSHConnection
from execution_registy import(get_execution, update_execution, fail_execution, finished_execution)

def execute_script(execution_id):
    execution = get_execution(execution_id)

    if execution is None:
        return
    
    node = execution["node"]
    folder = execution["folder"]
    script = execution["script"]
    runner = execution["runner"]

    ssh = SSHConnection(node)
    try :
        remote_script = f"/cortexlab/homes/{config.USERNAME}/{folder}/{script}"
        print(remote_script)
        log_path = f"/cortexlab/homes/{config.USERNAME}/{folder}/execution_{execution_id}.log"

        run_cmd = (
            f"{runner} {remote_script} 2>&1 | tee {log_path}"

        )
        stdout, stderr = ssh.run_on_node(run_cmd)
        print(stdout)
        output = ""
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

        finished_execution(execution_id=execution_id, result = result, stdout=output, stderr=error, log_path=log_path)
    except Exception as e:
        fail_execution(execution_id, error=str(e))
    finally:
        ssh.close()
