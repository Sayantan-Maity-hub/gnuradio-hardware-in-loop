import threading

registry = {}
lock = threading.Lock()


def update_node(node, data):

    with lock:
        existing_job = registry.get(node, {}).get("job", {})
        os_data = data.get("os", "")
        pretty = None
        if isinstance(os_data, str):
            for line in os_data.splitlines():
                if line.startswith("PRETTY_NAME="):
                    pretty = line.split("=", 1)[1].strip('"')
                    break

        registry[node] = {
            "hostname": data.get("hostname", node),
            "status": data.get("status", "OFFLINE"),
            "os": pretty,
            "job": existing_job,
        }


def update_job(node, **kwargs):
    with lock:
        if node not in registry:
            registry[node] = {
                "hostname": node,
                "status": "UNKNOWN",
                "os": None,
                "job": {},
                "execution_id": None,
            }
        job = registry[node].setdefault("job", {})
        for key, value in kwargs.items():
            if value is not None:
                job[key] = value


def clear_job(node):
    with lock:
        if node is registry:
            registry[node]["job"] = {}


def get_nodes():
    with lock:
        return dict(registry)


def get_node(node):
    with lock:
        return registry.get(node)
