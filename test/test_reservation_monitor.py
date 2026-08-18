from cortexlab.reservation.reservation_monitor import parse_assigned_nodes


def test_parse_assigned_nodes_does_not_read_the_next_oar_field():
    job_info = """assigned_hostnames =
queue = default
"""

    assert parse_assigned_nodes(job_info) == []


def test_parse_assigned_nodes_from_oar_hostname_line():
    job_info = "assigned_hostnames = mnode14.cortexlab.fr+mnode15.cortexlab.fr\n"

    assert parse_assigned_nodes(job_info) == ["node14", "node15"]
