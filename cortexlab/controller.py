import time
import threading
from reservation import reserve_nodes
from scenario_generator import (create_task, generate_scenario, submit_task, wait_for_task_running)
from monitor import monitor_nodes
from registry import get_nodes
from flask_server import start_flask
from cortexlab_remote import cortexlab_Remote

def main():
    print("\n Welcome to the cortexlab controller script")
    
    remote = cortexlab_Remote(hostname="gw.cortexlab.fr", username="sayantan_maity")
    
    #Remotely Reserve nodes via OAR resevation.py used here.
    job_id, nodes, walltime = reserve_nodes(remote)
    clean_nodes = []

    for n in nodes:
        short = n.split(".")[0]          # mnode14.cortexlab.fr → mnode14
        short = short.replace("mnode", "node")  # optional rename
        clean_nodes.append(short)
    nodes = clean_nodes
    print(nodes)


    #Generate scenario.yaml file for all the reserved nodes with no command just to start ssh server on node.
    generate_scenario(nodes, walltime)
    
    remote.upload_folder("cortexlab/scenario", "scenario")

    
    
    #Remotely Create a task using minus task create command.
    create_task(remote)

    #Remotely Submit the task using minus task submit command.
    task_id = submit_task(remote)
    #waiting for start task
    wait_for_task_running(remote, task_id)

    nodes = ["node14", "node16"]
    
    #Monitoring the nodes using monitor.py to check if they are online or offline.
    monitor_thread = threading.Thread(target=monitor_nodes, args=(nodes, 10), daemon=True) #threading to monitor the nodes in the background.
    monitor_thread.start()
    print("monitoring nodes started in the background.")
    
    flask_thread = threading.Thread(target = start_flask, daemon=True)
    flask_thread.start()
    print("Flask API available at:")
    print("http://localhost:5678/status/nodes")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Controller stopped.")

if __name__ == "__main__":
    main()



