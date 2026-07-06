import threading
registry = {}
lock = threading.Lock()
def update_node(node, data):
    
    with lock:
        existing_job = registry.get(node, {}).get("job",
                                                  {
                                                       "name":None,
                                                       "state":None,
                                                       "step": []
                                                  }
                                                )
        os_data = data.get("os", "")
        pretty = None
        if isinstance(os_data, str):
                    for line in os_data.splitlines():
                         if line.startswith("PRETTY_NAME="):
                              pretty = line.split("=", 1)[1].strip('"')
                              break

        registry[node]={
            "hostname": data.get("hostname", node),
            "status": data.get("status", "OFFLINE"),
            "os": pretty,
            "job": existing_job
        }
def update_job(node, job_id = None,  task_id=None, description=None, folder=None, script = None, state = None):
     with lock:
          if node not in registry:
               registry[node] = {
                    "hostname": node,
                    "status": "UNKNOWN",
                    "os": None,
                    "job": {}
               }
          registry[node]["job"] = {
               "job_id": job_id,
               "task_id": task_id,
               "description": description,
               "folder": folder,
               "script": script,
               "state": state,
          }
def clear_job(node):
     update_job(node = node, Job_id=None, task_id=None, description=None, folder=None, script= None, state=None)

def get_nodes():
    with lock:
        return dict(registry)

def get_node(node):
     with lock:
          return registry.get(node)

    
