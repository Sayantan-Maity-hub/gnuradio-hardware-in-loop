# GNU Radio Hardware-in-the-Loop Controller for CortexLab

This project is a Python controller for running repeatable GNU Radio **hardware-in-the-loop (HIL)** experiments on [CortexLab](https://www.cortexlab.fr/) radio nodes. It exposes a small HTTP API and dashboard that reserve real radio hardware, prepare an experiment, copy its scripts to the allocated nodes, run the transmitter and receiver together, and collect a final analysis result.

It is intended for development and validation of GNU Radio experiments that need real SDR hardware rather than only local simulation. The repository currently contains two example experiments:

- `basic_hardware_test` — a simple transmit/receive hardware test.
- `ofdm_hardware_test` — an OFDM transmit/receive example.

> **Project status:** the controller and example experiment workflow are under active development. The CI integration is **not complete**. The repository contains early Docker-image build tooling and example request scripts, but it does not yet contain a production CI workflow that automatically builds an image, deploys it, starts an experiment, and reports its result to a pull request.

## Why this project exists

Testing GNU Radio code on a developer machine cannot fully validate RF behavior, hardware drivers, timing, radio configuration, or interactions between physical transmitter and receiver nodes. CortexLab provides remotely reservable SDR nodes, but running a test manually requires several coordinated steps:

1. Reserve compatible nodes through CortexLab/OAR.
2. Create a CortexLab MINUS task so the nodes start the required GNU Radio container.
3. Copy the experiment scripts and parameters to the reservation workspace.
4. Start scripts on multiple nodes at approximately the same time.
5. Check that node execution completed and evaluate the captured result.

This controller puts those steps behind one request, keeps in-memory status registries, and provides endpoints/dashboard views for observing reservations, nodes, and experiments.

## How it works

```text
Client / CI request
       |
       v
Flask controller (:5678)
       |
       +--> OAR reservation + reservation monitor
       |
       +--> MINUS scenario/task using the configured GNU Radio image
       |
       +--> Select available nodes and create experiments/runs/<experiment-id>/
       |
       +--> Upload files over SSH/SFTP to CortexLab
       |
       +--> Start each node script together over node SSH
       |
       +--> Run analysis.py and download results.json
       |
       v
Status API and browser dashboard
```

An experiment ID is generated as `<pr-id>-<commit-sha-prefix>-<oar-job-id>`. If no commit SHA is supplied, `unknown` is used in its place.

## Repository layout

| Path | Purpose |
| --- | --- |
| `controller.py` | Starts the Flask controller. |
| `flask_server.py` | HTTP API and dashboard routes. |
| `config.py` | CortexLab connection settings, valid nodes, toolchain path, and default container image. |
| `cortexlab/reservation/` | OAR reservation submission, MINUS scenario creation, and reservation tracking. |
| `cortexlab/nodes/` | In-memory node status and availability tracking. |
| `cortexlab/execution/` | Remote node-script execution, synchronization, result tracking, and analysis execution. |
| `experiment_manager/` | Creates run folders, uploads them, and coordinates an experiment lifecycle. |
| `experiment_manager/hil_experiments/` | Experiment definitions and their node scripts, parameter examples, and analysis scripts. |
| `experiments/runs/` | Locally generated copies of individual experiment runs and downloaded artifacts. |
| `ci_workflow/` | Incomplete CI-related Docker build tooling and example API requests. |
| `test/` | Automated tests for controller components. |

## Prerequisites

Before using the controller, you need:

- Python 3.10 or newer.
- Access to CortexLab, including a gateway hostname and username.
- An SSH key accepted by CortexLab. The current connection implementation reads `C:\Users\maity\.ssh\id_ed25519`.
- Permission to reserve the nodes listed in `config.py`.
- A CortexLab-compatible GNU Radio container image. The default is configured in `config.DEFAULT_BASE_IMAGE`.
- Network access to the CortexLab gateway and allocated nodes.

This project interacts with real shared hardware. Use a short walltime while developing, choose an informative reservation name, and only run experiments you are authorized to run.

## Installation

Clone the repository, then create and activate a virtual environment.

```powershell
git clone <your-repository-url>
cd gnuradio-hardware-in-loop
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure the values in `config.py` before sending a request:

```python
USERNAME = "your_cortexlab_username"
HOSTNAME = "gw.cortexlab.fr"
CORTEXLAB_VALID_NODES = [14, 15]
```

Alternatively, `username` and `hostname` can be provided in a `POST /run-experiment` request; the controller stores them for the current process. Do not commit personal usernames, private keys, passwords, or registry credentials.

## Start the controller

Run:

```powershell
python controller.py
```

The API and dashboard are then available at:

- Dashboard: `http://127.0.0.1:5678/`
- API base: `http://127.0.0.1:5678/`

Keep this process running until the experiment finishes. The reservation, node, and execution registries are currently in memory, so restarting the controller loses their tracked status.

## Run an experiment

Send a JSON request to `POST /run-experiment`. The request reserves nodes if no active reservation is being reused, waits for node status, and runs the selected experiment.

```powershell
$request = @{
    hostname         = "gw.cortexlab.fr"
    username         = "your_cortexlab_username"
    walltime         = "00:30:00"
    reservation_name = "basic-hil-test"
    experiment       = "basic_hardware_test"
    pr_id            = 123
    source           = @{
        repository = "owner/repository"
        commit_sha = "0123456789abcdef0123456789abcdef01234567"
    }
    parameter        = @{
        duration         = 5
        sample_rate      = 1000000
        gain             = 20
        capture_samples  = 5000000
        center_frequency = 1000000
        tone_frequency   = 100000
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Uri "http://127.0.0.1:5678/run-experiment" `
    -Method POST `
    -ContentType "application/json" `
    -Body $request
```

Parameter examples are stored with each experiment:

- `experiment_manager/hil_experiments/basic_hardware_test/parameter.json`
- `experiment_manager/hil_experiments/ofdm_hardware_test/parameter.json`

The `ci_workflow/example_experiment_request/` files provide additional PowerShell request examples despite their `.sh` filenames.

### Request fields

| Field | Required | Description |
| --- | --- | --- |
| `hostname` | Yes* | CortexLab gateway hostname. |
| `username` | Yes* | CortexLab username. |
| `walltime` | Yes | Reservation duration in `HH:MM:SS`. |
| `reservation_name` | Yes | Human-readable name used for the OAR reservation and MINUS task. |
| `experiment` | Yes | Directory name under `experiment_manager/hil_experiments/`. |
| `pr_id` | Yes | Pull-request or external run identifier used in the experiment ID. |
| `parameter` | Yes | JSON object written to `parameters.json` for the experiment. |
| `source` | No | Metadata such as `repository` and `commit_sha`; the SHA is included in the experiment ID. |

\* These are required either in the request or already configured in `config.py`.

## Monitor a run

Use the dashboard or the following endpoints while the controller is running:

| Endpoint | Description |
| --- | --- |
| `GET /status/reservations` | All reservations tracked by this controller process. |
| `GET /status/reservations/<job_id>` | One reservation and its task/node details. |
| `GET /status/nodes` | Tracked nodes, availability, and assigned experiment IDs. |
| `GET /status/experiments` | All tracked experiment executions. |
| `GET /status/experiment/<experiment_id>` | One experiment execution. |

The dashboard refreshes these views every two seconds.

## Create an experiment

Each experiment lives below `experiment_manager/hil_experiments/<experiment-name>/` and needs this layout:

```text
my_experiment/
├── node_scripts/
│   ├── tx.py
│   └── rx.py
├── analysis.py
└── parameter.json
```

- Every `*.py` file in `node_scripts/` is assigned to one available CortexLab node. Two scripts therefore need two available nodes.
- The controller copies each script into its node-specific run folder and uploads all files to the CortexLab reservation workspace.
- Node scripts are made executable, started through the CortexLab GNU Radio toolchain, and synchronized with a barrier plus a common start time.
- `analysis.py` runs after the primary node scripts finish successfully. It should create `results.json` in the experiment root on CortexLab.
- The controller downloads `results.json` into `experiments/runs/<experiment-id>/` and treats `{"status": "passed"}` as a passing final result. Any other status is recorded as failure.

The node scripts are responsible for reading `parameters.json`, configuring their radios safely, and returning a useful exit code.

## CI and custom GNU Radio images — current status

The intended CI direction is to validate a GNU Radio revision or pull request against physical CortexLab hardware:

1. Build a CortexLab-compatible image containing the requested GNU Radio revision.
2. Push that image to a registry accessible from CortexLab.
3. Start the controller and submit an experiment request with PR/commit metadata.
4. Collect the HIL result and publish it back to the CI system or pull request.

The repository currently provides partial building blocks:

- `ci_workflow/build_gnuradio_image.py` can build, verify, and optionally push an image from a GNU Radio commit SHA.
- `ci_workflow/docker_image/Dockerfile.pr` can build a CortexLab toolchain image from `GNURADIO_REF`.
- `ci_workflow/example_experiment_request/` contains manual request examples.

The following CI pieces are still missing or need integration and verification:

- No GitHub Actions, GitLab CI, or other CI pipeline definition is included.
- The requested image is not yet passed from a CI request into MINUS scenario generation; scenarios currently use `DEFAULT_BASE_IMAGE` from `config.py`.
- Registry authentication, image naming/tagging, and image availability to CortexLab are not automated.
- CI result reporting back to the source pull request is not implemented.
- End-to-end CI runs against CortexLab still need validation, including cleanup/failure handling and secrets management.

For now, use the image builder manually and set `DEFAULT_BASE_IMAGE` to an image CortexLab can pull before submitting an experiment.

Example manual image build:

```powershell
python ci_workflow/build_gnuradio_image.py `
    --sha <gnu-radio-commit-sha> `
    --image <registry>/gnuradio-hil:<tag> `
    --push
```

Docker must be installed, running, and authenticated to the target registry for this command.

## Tests

Run the automated test suite with:

```powershell
pytest
```

The tests cover local controller logic; they are not a substitute for a real CortexLab HIL run.

## Current limitations

- The controller is designed around a local Windows development setup and currently has a hard-coded private-key path in the SSH connection code.
- Status registries are in memory only; they are not durable across restarts and are not intended for concurrent production use.
- The controller has no authentication or authorization layer. Do not expose port 5678 to an untrusted network.
- Experiment folders are generated under `experiments/runs/`; review and clean old artifacts as appropriate for your environment.
- Hardware availability, RF conditions, and remote-service behavior can affect experiment outcomes.

## Contributing

When adding an experiment, include its node scripts, a parameter example, an analysis script that writes `results.json`, and tests where the behavior can be tested locally. Keep credentials and generated run artifacts out of commits.
