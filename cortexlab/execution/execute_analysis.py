"""Execute analysis script after all node script execution finished calling from excution_monitor _finish_experiment_if_complete function.

it load the analysis
"""

import os
import json
import time

from cortexlab.remote_connections.cortexlab_remote import cortexlab_Remote
import config
from .execution_registy import get_execution, update_execution


def execute_analysis(experiment_id):

    experiment = get_execution(experiment_id)

    if experiment is None:
        return

    folder = experiment.get("folder")
    analysis_script = experiment.get("analysis_script")

    if not folder and analysis_script:
        update_execution(
            experiment_id,
            state="FAILED",
            overall_result="FAILED",
            stderr="Experiment remote folder or analysis srcipt not found",
        )
        return

    remote = cortexlab_Remote()

    try:

        remote_dir = f"/cortexlab/homes/{config.USERNAME}/{folder}"

        remote_analysis = f"{remote_dir}/{analysis_script}"

        remote_result = f"{remote_dir}/results.json"

        print(f"Running analysis: {remote_analysis}")

        # Run analysis.py
        stdout, stderr = remote.run(f"cd {remote_dir} && python3 {analysis_script}")

        output = stdout.read().decode()
        error = stderr.read().decode()

        print("Analysis output:")
        print(output)

        # Check analysis execution
        exit_code = stdout.channel.recv_exit_status()

        if exit_code != 0:

            update_execution(
                experiment_id,
                state="FAILED",
                overall_result="FAILED",
                stderr=error or output,
                ended=time.strftime("%Y-%m-%d %H:%M:%S"),
            )

            return

        # Local results path
        local_experiment_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "experiments",
            "runs",
            str(experiment_id),
        )

        os.makedirs(
            local_experiment_dir,
            exist_ok=True,
        )

        local_result = os.path.join(
            local_experiment_dir,
            "results.json",
        )

        # Download results.json
        print(
            f"Downloading analysis result Remote: {remote_result} Local : {local_result}"
        )

        remote.download_file(remote_result, local_result)

        # Read result
        with open(
            local_result,
            "r",
            encoding="utf-8",
        ) as f:
            result = json.load(f)

        print(f"Analysis result: {result}")

        # Determine final result
        if result.get("status") == "passed":

            update_execution(
                experiment_id,
                state="FINISHED",
                overall_result="PASS",
                experiment_result=result,
                ended=time.strftime("%Y-%m-%d %H:%M:%S"),
            )

        else:
            update_execution(
                experiment_id,
                state="FAILED",
                overall_result="FAILED",
                experiment_result=result,
                ended=time.strftime("%Y-%m-%d %H:%M:%S"),
            )

        return result.get("status")

    except Exception as error:
        print(f"Analysis failed for {experiment_id}: {error}")

        update_execution(
            experiment_id,
            state="FAILED",
            overall_result="FAILED",
            stderr=str(error),
            ended=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    finally:
        remote.close()
