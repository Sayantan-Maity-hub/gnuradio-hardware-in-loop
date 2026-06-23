import threading
from reservation import reserve_nodes
from scenario_generator import (create_task, generate_scenario, submit_task)
from monitor import monitor_nodes

def main():
    print("\n Welcome to the cortexlab controller script")

    #Reserve nodes via OAR resevation.py used here.
    job_id, nodes = reserve_nodes()
    print(job_id)
    print(nodes)

    for node in nodes:
        print(node)

