from pathlib import Path


# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Experiment manager directory
EXPERIMENT_MANAGER_ROOT = PROJECT_ROOT / "experiment_manager"

# Same location used by generic_experiment_runner.py
EXPERIMENTS_ROOT = EXPERIMENT_MANAGER_ROOT


def test_experiment(experiment_name):

    print("=" * 70)
    print("GENERIC EXPERIMENT RUNNER - PATH TEST")
    print("=" * 70)

    print(f"\nProject root:")
    print(f"  {PROJECT_ROOT}")

    print(f"\nExperiment manager:")
    print(f"  {EXPERIMENT_MANAGER_ROOT}")

    print(f"\nEXPERIMENTS_ROOT:")
    print(f"  {EXPERIMENTS_ROOT}")

    # Check experiment directory

    experiment_dir = (EXPERIMENTS_ROOT / "hil_experiments" / experiment_name)

    print(f"\nExperiment directory:")
    print(f"  {experiment_dir}")

    if not experiment_dir.is_dir():
        print("\n FAIL: Experiment directory not found")
        return False

    print("PASS: Experiment directory exists")

    # Check node_scripts directory

    node_dir = experiment_dir / "node_scripts"

    print(f"\nNode scripts directory:")
    print(f"  {node_dir}")

    if not node_dir.is_dir():
        print("\n FAIL: node_scripts directory not found")
        return False

    print("PASS: node_scripts directory exists")

    # Find Python node scripts

    node_scripts = sorted(file for file in node_dir.iterdir() if file.is_file() and file.suffix == ".py")

    print("\nNode scripts:")

    if not node_scripts:
        print(" No Python node scripts found")
        return False

    for script in node_scripts:
        print(f"{script.name}")

    print(f"\nTotal node scripts: {len(node_scripts)}")

    # Check analysis.py

    analysis_script = experiment_dir / "analysis.py"

    print(f"\nAnalysis script:")
    print(f"  {analysis_script}")

    if not analysis_script.is_file():
        print("\n FAIL: analysis.py not found")
        return False

    print(" PASS: analysis.py exists")

    # Final result

    print("\n" + "=" * 70)
    print(" ALL TESTS PASSED")
    print("=" * 70)

    return True


if __name__ == "__main__":

    success = test_experiment("basic_hardware_test")

    if not success:
        raise SystemExit(1)