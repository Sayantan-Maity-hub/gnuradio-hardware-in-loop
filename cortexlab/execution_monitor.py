import threading
import re
import config
from ssh_client import SSHConnection
from execution_monitor import(start_execution, finish_execution, fail_execution, update_execution)

def execute_script(node, folder, script, runner):
    ssh = SSHConnection(node)
    try :
        remote_script = f"/cortexlab/homes/{config.USERNAME}/{folder}/{node}/{script}"
        run_cmd = (
            f"{runner} {remote_script} 2>&1 | tee {remote_script}/execution.log"

        )
        stdout, stderr = ssh.run_on_node(run_cmd)
        output = ""
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line, end="")
            output += line
            update_execution(node, stdout = output)
            error = stderr.read().decode()
            if error:
                update_execution(node, stderr=error)
            exit_code = stdout.channel.recv_exit_status()
            result = "UNKWON"
            match = re.search(r"::STATUS:.*:(PASS|FAIL):", output)
            if match:
                result = match.group(1)
            elif exit_code == 0:
                result = "SUCCESS"
            else:
                result = "FAILED"

            finish_execution(node = node, result = result, stdout=output, stderr=error)
    except Exception as e:
        fail_execution(node, error=str(e))
    finally:
        ssh.close()
