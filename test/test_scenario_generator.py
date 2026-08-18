import yaml
from cortexlab.reservation.reservation_task_creation import generate_scenario

# ===================================== TEST===========================================


def test_scenario_generation():
    nodes = ["mnode14.cortexlab.fr", "mnode21.cortexlab.fr"]

    generate_scenario("scenario", nodes, 600, "Controller Test")

    with open("scenario/scenario.yaml") as f:
        data = yaml.safe_load(f)
    assert data["description"] == "Controller Test"
    assert len(data["nodes"]) == 2
