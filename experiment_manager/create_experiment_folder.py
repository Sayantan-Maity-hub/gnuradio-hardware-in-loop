import os
import shutil
import json
from cortexlab.execution.execution_registy import update_execution


def create_experiment_folder( experiment_id, node_files, parameters, root_files = None):

    # Find project root
    
    if root_files is None:
        root_files =[]

    current_file = os.path.abspath(__file__)

    project_root = os.path.abspath(os.path.join(os.path.dirname(current_file), ".."))

    # Experiment base directory

    base_folder = os.path.join(project_root, "experiments", "runs")

    # Make sure experiments/runs exists
    os.makedirs(base_folder, exist_ok=True)

    # Experiment directory

    experiment_folder = os.path.join(base_folder, str(experiment_id))


    # Create clean experiment directory

    if os.path.exists(experiment_folder):
        print(f"Removing existing experiment folder: {experiment_folder}")

        shutil.rmtree(experiment_folder)

    os.makedirs(experiment_folder, exist_ok=True)

    for file_path in root_files:

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Experiment root file not found: {file_path}")

        destination = os.path.join(
            experiment_folder,
            os.path.basename(file_path))

        print(f"Copy root file: {file_path} -> {destination}")

        shutil.copy2(file_path, destination)

    # Create node folders and copy files

    for node, files in node_files.items():

        node_folder = os.path.join(experiment_folder, str(node))

        os.makedirs(node_folder, exist_ok=True)

        # Make sure files is iterable
        if isinstance(files, str):
            files = [files]

        for file_path in files:

            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Experiment file not found: {file_path}")

            destination = os.path.join(node_folder, os.path.basename(file_path))

            shutil.copy2(file_path, destination)

            print(f"Copied: {file_path} -> {destination}")


    # Create parameters.json

    parameters_file = os.path.join(experiment_folder, "parameters.json")

    with open(parameters_file, "w", encoding="utf-8") as f:

        json.dump(parameters, f, indent=4)

    #update execution registry
    updated = update_execution(experiment_id, local_folder=experiment_folder)
    if not updated:
        raise RuntimeError(f"Experiment {experiment_id} not found in execution registry")

    # Print result

    print(f"Experiment folder created: {experiment_folder}")

    print(f"Parameters file created: {parameters_file}")

    return experiment_folder