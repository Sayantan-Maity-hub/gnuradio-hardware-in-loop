import threading
import time

execution_registry = {}
lock = threading.Lock()

def update_execution(node, **kwargs):
    with lock:
        if node not in execution_registry:

            execution_registry[node] = {


                "script": None,

                "command":None,

                "state": "IDLE",

                "result":"",

                "stdout":"",

                "stderr":"",

                "log_path":None,

                "started":None,

                "ended":None

            }
        
        execution_registry[node].update(kwargs)

def finished_execution(node, result, stdout, stderr):
    update_execution(node, state="FINISHED", result=result, stdout = stdout, stderr = stderr, ended = time.strftime("%Y-%m-%d %H:%M:%S"))

def fail_execution(node, error):
    update_execution(node, state="ERROR", stderr = str(error), ended=time.strftime("%Y-%m-%d %H:%M:%S"))

def clear_execution(node):
    with lock:
        execution_registry[node] = {
            "script": None,
            "command": None,
            "state": "IDLE",
            "result": None,
            "stdout": "",
            "stderr": "",
            "log_file": None,
            "started": None,
            "ended": None
        }

def get_execution(node):
    with lock:
        return execution_registry.get(node)
    
def get_all_execution():
    with lock:
        return dict(execution_registry)