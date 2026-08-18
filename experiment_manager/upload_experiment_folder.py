import os

from cortexlab.remote_connections.cortexlab_remote import cortexlab_Remote
from cortexlab.execution.execution_registy import update_execution


def upload_experiment_folder(job_id, experiment_id, local_folder):
    
    # Validate local experiment folder
    

    if not os.path.isdir(local_folder):
        raise FileNotFoundError(f"Experiment folder not found: {local_folder}")

    # Remote experiment folder

    remote_folder = (f"{job_id}/{experiment_id}")

    # Update execution registry

    updated = update_execution(experiment_id, folder=remote_folder,)

    if not updated:

        raise RuntimeError(f"Experiment {experiment_id} not found in execution registry")

    remote = cortexlab_Remote()

    try:

        print(f"Uploading experiment {experiment_id}...")

        print(f"Local folder : {local_folder}")

        print(f"Remote folder: {remote_folder}")


        # Upload complete experiment folder

        remote.upload_folder(local_folder, remote_folder,)

        print(f"Experiment {experiment_id} uploaded successfully")

    except Exception:
        
        print(f"Failed to upload experiment {experiment_id}")
        raise

    finally:
        remote.close()

    return remote_folder