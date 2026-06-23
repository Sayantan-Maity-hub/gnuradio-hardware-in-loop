import subprocess
def hostname_to_scenario_name(host):
    short=host.split(".")[0]
    return short.replace("mnode", "node")

def create_task():
    subprocess.run("minus task create", shell=True, check=True)
