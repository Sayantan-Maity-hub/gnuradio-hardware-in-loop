import time
import threading
from reservation import reserve_nodes
from scenario_generator import (create_task, generate_scenario, submit_task, wait_for_task_running)
from monitor import monitor_nodes
from registry import get_nodes
from flask_server import start_flask
from cortexlab_remote import cortexlab_Remote
import config

def main():

    print("\n Welcome to the cortexlab controller script")

    config.USERNAME = input("Enter your username: \n")
    config.HOSTNAME = input("Enter the hostname: \n")
    
    remote = cortexlab_Remote()

    #Remotely Reserve nodes via OAR resevation.py used here.
    reserve_nodes()
    
    clean_nodes = []

    for n in nodes:
        short = n.split(".")[0]          
        short = short.replace("mnode", "node") 
        clean_nodes.append(short)
    nodes = clean_nodes
    config.NODES = nodes
    print(nodes)




    #Generate scenario.yaml file for all the reserved nodes with no command just to start ssh server on node.
    job_folder = str(config.JOB_ID)
    generate_scenario(job_folder, nodes, config.WALLTIME)
    
    remote.upload_folder(job_folder, job_folder)

    
    #Remotely Create a task using minus task create command.
    create_task(remote, job_folder)

    #Remotely Submit the task using minus task submit command.
    config.TASK_ID = submit_task(remote, job_folder)
    #waiting for start task
    wait_for_task_running(remote, config.TASK_ID)

    
    
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
