import time
import threading
from flask_server import start_flask
from reservation_monitor import reservation_monitor


def main():

    print("\n Welcome to the cortexlab controller script")

    flask_thread = threading.Thread(target = start_flask, daemon=True)
    flask_thread.start()
    print("Flask API available at:")
    print("http://localhost:5678/status/nodes")


    '''

    #Node state monitor thread
    reservations = get_all_reservation()
    for job_id, reservation in reservations.items():
        if (reservation["state"] == "Running" and reservation["assigned_nodes"]):
            nodes = reservation["assigned_nodes"]
            monitor_thread = threading.Thread(target=monitor_nodes, args=(nodes, 10), daemon=True) #threading to monitor the nodes in the background.
            monitor_thread.start()
            print("monitoring nodes started in the background.")
    


    
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

    
    '''
    #Monitoring the nodes using monitor.py to check if they are online or offline.
    
   
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Controller stopped.")

if __name__ == "__main__":
    main()
