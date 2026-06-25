import threading
from reservation import reserve_nodes
from scenario_generator import (create_task, generate_scenario, submit_task)
from monitor import monitor_nodes
from registry import get_nodes
from flask_server import start_flask

def main():
    print("\n Welcome to the cortexlab controller script")

    #Reserve nodes via OAR resevation.py used here.
    job_id, nodes, walltime = reserve_nodes()
    print(job_id)
    print(nodes)

    for node in nodes:
        print(node)

    #Generate scenario.yaml file for all the reserved nodes with no command just to start ssh server on node.
    generate_scenario(nodes, walltime)

    #Create a task using minus task create command.
    create_task()

    #Submit the task using minus task submit command.
    submit_task()

    #Monitoring the nodes using monitor.py to check if they are online or offline.
    monitor_thread = threading.Thread(target=monitor_nodes, args=(nodes, 30), daemon=True) #threading to monitor the nodes in the background.
    monitor_thread.start()
    print("monitoring nodes started in the background.")
    
    flask_thread = threading.Thread(target = start_flask, daemon=True)
    flask_thread.start()
    print("Flask API available at: ")
    print("https://localhost:5678/status/nodes")

if __name__ == "__main__":
    main()



