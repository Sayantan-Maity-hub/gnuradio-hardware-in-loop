import os
import json
import tempfile

from create_experiment_folder import create_experiment_folder
from cortexlab.execution.execution_registy import update_execution


def print_tree(directory, prefix=""):
    """Print directory tree."""
    if not os.path.exists(directory):
        print(f"{prefix}[NOT FOUND] {directory}")
        return

    print(f"{prefix}{os.path.basename(directory)}/")

    entries = sorted(os.listdir(directory))

    for index, entry in enumerate(entries):
        path = os.path.join(directory, entry)

        is_last = index == len(entries) - 1
        connector = "└── " if is_last else "├── "

        if os.path.isdir(path):
            print(f"{prefix}{connector}{entry}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree_contents(path, new_prefix)
        else:
            print(f"{prefix}{connector}{entry}")


def print_tree_contents(directory, prefix):
    """Print contents of an already printed directory."""
    entries = sorted(os.listdir(directory))

    for index, entry in enumerate(entries):
        path = os.path.join(directory, entry)

        is_last = index == len(entries) - 1
        connector = "└── " if is_last else "├── "

        if os.path.isdir(path):
            print(f"{prefix}{connector}{entry}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree_contents(path, new_prefix)
        else:
            print(f"{prefix}{connector}{entry}")


def main():

    print("=" * 70)
    print("TEST: create_experiment_folder()")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Test experiment ID
    # ---------------------------------------------------------

    experiment_id = "TEST_CREATE_FOLDER_001"

    print(f"\n[1] Experiment ID: {experiment_id}")

    # ---------------------------------------------------------
    # 2. Create temporary source files
    # ---------------------------------------------------------

    print("\n[2] Creating temporary input files...")

    with tempfile.TemporaryDirectory() as temp_dir:

        tx_file = os.path.join(temp_dir, "tx.py")
        rx_file = os.path.join(temp_dir, "rx.py")
        analysis_file = os.path.join(temp_dir, "analysis.py")
        scenario_file = os.path.join(temp_dir, "scenario.yaml")

        test_files = {
            tx_file: "# TX test file\n",
            rx_file: "# RX test file\n",
            analysis_file: "# Analysis test file\n",
            scenario_file: "name: test-scenario\n",
        }

        for path, content in test_files.items():
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"  Created: {path}")

        # -----------------------------------------------------
        # 3. Prepare input for create_experiment_folder()
        # -----------------------------------------------------

        node_files = {
            "node26": [
                tx_file,
            ],
            "node38": [
                rx_file,
            ],
        }

        root_files = [
            analysis_file,
            scenario_file,
        ]

        parameters = {
            "sample_rate": 1_000_000,
            "frequency": 100_000,
            "samples": 5_000_000,
            "test": "create_experiment_folder",
        }

        # -----------------------------------------------------
        # 4. Make sure execution registry contains experiment
        # -----------------------------------------------------

        print("\n[3] Preparing execution registry...")

        try:
            registry_result = update_execution(
                experiment_id,
                status="CREATED"
            )

            print(f"  update_execution() result: {registry_result}")

        except TypeError:
            print(
                "  WARNING: update_execution() does not accept "
                "status parameter."
            )
            print(
                "  The test will continue, but the registry may need "
                "the experiment to exist beforehand."
            )

        # -----------------------------------------------------
        # 5. Call function
        # -----------------------------------------------------

        print("\n[4] Calling create_experiment_folder()...")
        print("-" * 70)

        try:

            experiment_folder = create_experiment_folder(
                experiment_id=experiment_id,
                node_files=node_files,
                parameters=parameters,
                root_files=root_files,
            )

        except Exception as e:

            print("\n❌ TEST FAILED")
            print(f"Error: {type(e).__name__}: {e}")

            print("\nTemporary input directory:")
            print_tree(temp_dir)

            raise

        # -----------------------------------------------------
        # 6. Verify experiment directory
        # -----------------------------------------------------

        print("\n" + "-" * 70)
        print("[5] Verifying created experiment directory...")
        print("-" * 70)

        if not os.path.isdir(experiment_folder):
            raise AssertionError(
                f"Experiment folder was not created: {experiment_folder}"
            )

        print(f"✅ Experiment folder exists:")
        print(f"   {experiment_folder}")

        # -----------------------------------------------------
        # 7. Verify root files
        # -----------------------------------------------------

        print("\n[6] Checking root files...")

        expected_root_files = [
            "analysis.py",
            "scenario.yaml",
            "parameters.json",
        ]

        for filename in expected_root_files:

            path = os.path.join(experiment_folder, filename)

            if os.path.isfile(path):
                print(f"  ✅ {filename}")
            else:
                print(f"  ❌ {filename}")
                raise AssertionError(
                    f"Missing root file: {path}"
                )

        # -----------------------------------------------------
        # 8. Verify node folders
        # -----------------------------------------------------

        print("\n[7] Checking node folders...")

        expected_nodes = {
            "node26": ["tx.py"],
            "node38": ["rx.py"],
        }

        for node, files in expected_nodes.items():

            node_folder = os.path.join(
                experiment_folder,
                node
            )

            if not os.path.isdir(node_folder):
                raise AssertionError(
                    f"Node folder missing: {node_folder}"
                )

            print(f"  ✅ {node}/")

            for filename in files:

                path = os.path.join(
                    node_folder,
                    filename
                )

                if os.path.isfile(path):
                    print(f"      ✅ {filename}")
                else:
                    raise AssertionError(
                        f"Missing file: {path}"
                    )

        # -----------------------------------------------------
        # 9. Verify parameters.json
        # -----------------------------------------------------

        print("\n[8] Checking parameters.json...")

        parameters_file = os.path.join(
            experiment_folder,
            "parameters.json"
        )

        with open(
            parameters_file,
            "r",
            encoding="utf-8"
        ) as f:
            saved_parameters = json.load(f)

        if saved_parameters != parameters:
            raise AssertionError(
                "parameters.json content does not match input parameters"
            )

        print("  ✅ parameters.json content is correct")

        # -----------------------------------------------------
        # 10. Print final directory tree
        # -----------------------------------------------------

        print("\n" + "=" * 70)
        print("FINAL EXPERIMENT DIRECTORY TREE")
        print("=" * 70)

        print_tree(experiment_folder)

        # -----------------------------------------------------
        # 11. Final result
        # -----------------------------------------------------

        print("\n" + "=" * 70)
        print("✅ TEST PASSED")
        print("=" * 70)

        print(f"\nExperiment directory:")
        print(experiment_folder)


if __name__ == "__main__":
    main()