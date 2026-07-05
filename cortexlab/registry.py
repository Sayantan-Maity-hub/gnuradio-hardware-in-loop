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
            "hostname": data.get("hostname"),
            "status": data.get("status"),
            "os": pretty,
            "job": existing_job
        }
def update_job(node, name = None, state = None, steps = None):
     with lock:
          if node not in registry:
               registry[node] = {
                    "hostname": node,
                    "status": "UNKNOWN",
                    "os": None,
                    "job": {}
               }
          registry[node]["job"] = {
               "name": name,
               "state": state,
               "step": steps or []

          }
    
def get_nodes():
    print(dict(registry))
    with lock:
        return dict(registry)

def get_node(node):
     with lock:
          return registry.get(node)

    
