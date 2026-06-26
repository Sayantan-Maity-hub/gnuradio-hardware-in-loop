import yaml
from scenario_generator import generate_scenario

# ===================================== TEST===========================================

def test_scenario_generation():
    nodes = ["mnode14.cortexlab.fr", "mnode21.cortexlab.fr"]

    generate_scenario(nodes, 600)

    with open("scenario/scenario.yaml") as f:
        data = yaml.safe_load(f)
    assert data["description"] == "Controller Test"
    assert len(data["nodes"]) == 2

