import threading
import time

execution_registry = {}
lock = threading.Lock()

next_execution_id = 1

def create_execution(job_id, task_id, node, script, command):
    global next_execution_id
    with lock:
        execution_id = next_execution_id
        next_execution_id +=1
        
        execution_registry[execution_id] = {
            "job_id": job_id,
            "task_id": task_id,
            "node": node,
            "script": script,
            "command": command,
            "state": "RUNNING",
            "result":None,
            "stdout":"",
            "stderr":"",
            "log_path":None,
            "started":time.strftime("%Y-%m-%d %H:%M:%S"),
            "ended":None
        }
        return execution_id
        
def update_execution(execution_id, **kwargs):
        with lock:
            if execution_id not in execution_registry:
                return False
            execution_registry[execution_id].update(kwargs)
            return True

def finished_execution(execution_id, result, stdout, stderr, log_path):
    update_execution(execution_id, state="FINISHED", result=result, stdout = stdout, stderr = stderr, log_path = log_path, ended = time.strftime("%Y-%m-%d %H:%M:%S"))

def fail_execution(execution_id, error):
    update_execution(execution_id, state="ERROR", stderr = str(error), ended=time.strftime("%Y-%m-%d %H:%M:%S"))

def clear_execution(execution_id):
    with lock:
        execution_registry[execution_id] = {execution_registry.pop(execution_id, None)}

def get_execution(execution_id):
    with lock:
        return execution_registry.get(execution_id)
    
def get_all_execution():
    with lock:
        return dict(execution_registry)