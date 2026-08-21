import time
from pathlib import Path

from cortexlab.nodes.node_registry import is_node_busy, update_node, get_nodes

from cortexlab.execution.execution_registy import (
    create_experiment_registry,
    get_execution,
    update_execution,
)

from .create_experiment_folder import create_experiment_folder

from .upload_experiment_folder import upload_experiment_folder

from .start_experiment import start_experiment

from cortexlab.execution.execution_monitor import finish_experiment_if_complete
from cortexlab.execution.execute_analysis import execute_analysis

EXPERIMENTS_ROOT = Path(__file__).resolve().parent


def run_generic_experiment(experiment_name, job_id, pr_id, parameter):
    """
    Generic experiment runner.

    Experiment directory structure:

        experiments/
            <experiment_name>/
                node/
                    tx.py
                    rx.py
                    monitor.py
                analysis.py


    Every Python file inside node/ is treated as one independent node script.

    analysis.py is executed only after all primary
    node scripts finish successfully.
    """

    # Experiment ID

    experiment_id = f"{pr_id}-{job_id}"

    # Find experiment directory

    experiment_dir = EXPERIMENTS_ROOT / "hil_experiments" / experiment_name

    if not experiment_dir.is_dir():

        raise ValueError(f"Experiment directory not found: {experiment_dir}")

    # Node directory

    node_dir = experiment_dir / "node_scripts"

    if not node_dir.is_dir():

        raise ValueError(f"Node directory not found: {node_dir}")

    # Find node scripts

    node_scripts = sorted(
        [file for file in node_dir.iterdir() if file.is_file() and file.suffix == ".py"]
    )

    if not node_scripts:

        raise ValueError(f"No Python node scripts found in {node_dir}")

    required_nodes = len(node_scripts)

    print(f"Experiment {experiment_name} requires {required_nodes} nodes")

    print("Node scripts:", [script.name for script in node_scripts])

    # Find available CortexLab nodes

    all_nodes = get_nodes()

    available_nodes = []

    for node_name, node_info in all_nodes.items():

        if node_info.get("status") != "ONLINE":
            continue

        if is_node_busy(node_name):
            continue

        available_nodes.append(node_name)

    # Check node availability

    if len(available_nodes) < required_nodes:

        raise RuntimeError(
            f"Experiment requires {required_nodes} nodes, but only {len(available_nodes)} are available"
        )

    selected_nodes = available_nodes[:required_nodes]

    print(f"Selected nodes: {selected_nodes}")

    # Create node -> script mapping

    nodes_script = {}

    node_files = {}

    for node_name, script_path in zip(selected_nodes, node_scripts):

        nodes_script[node_name] = script_path.name

        node_files[node_name] = [str(script_path)]

        print(f"{node_name} -> {script_path.name}")

    # Mark nodes busy

    for node_name in selected_nodes:

        update_node(
            node_name,
            experiment_id=experiment_id,
            busy=True,
        )

    # Analysis script

    analysis_script = experiment_dir / "analysis.py"

    if not analysis_script.is_file():

        raise ValueError(f"analysis.py not found in {experiment_dir}")

    # analysis.py lives directly inside experiment root

    root_files = [str(analysis_script)]

    # Create experiment registry

    create_experiment_registry(
        experiment_id=experiment_id,
        experiment_name=experiment_name,
        nodes=nodes_script,
        analysis_script="analysis.py",
    )

    try:

        # Create local experiment run folder

        print("STEP 1: creating experiment folder")

        experiment_folder = create_experiment_folder(
            experiment_id=experiment_id,
            node_files=node_files,
            root_files=root_files,
            parameters=parameter,
        )

        print(f"STEP 1: folder created {experiment_folder}")

        # Upload to CortexLab

        print("STEP 2: uploading experiment")

        remote_folder = upload_experiment_folder(
            job_id=job_id,
            experiment_id=experiment_id,
            local_folder=experiment_folder,
        )

        print(f"STEP 2: upload done {remote_folder}")

        # Start primary node scripts

        print("STEP 3: starting experiment")

        result = start_experiment(
            experiment_id=experiment_id,
            job_id=job_id,
        )

        print(f"STEP 3: experiment started {result}")

        # Check all node in finished state
        finished_node_execution = finish_experiment_if_complete(experiment_id)

        # Free all node after used
        experiment = get_execution(experiment_id)

        nodes = experiment.get("nodes", {})

        for node_name in nodes:

            update_node(node_name, experiment_id=None, busy=False)

            print(f"Released node {node_name} from experiment {experiment_id}")

        # Analysis Results
        if finished_node_execution:
            analysis_result = execute_analysis(experiment_id)

        return analysis_result

    except Exception as e:

        print(f"Experiment {experiment_id} failed: {e}")

        update_execution(
            experiment_id,
            state="FAILED",
            overall_result="FAILED",
            stderr=str(e),
            ended=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        return get_execution(experiment_id)
