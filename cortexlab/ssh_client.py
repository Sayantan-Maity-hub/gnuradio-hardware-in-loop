import paramiko
import shlex
import os

class SSHConnection:
    def __init__(self, host):
        self.node_host=host.split(".")[0]
        key = paramiko.Ed25519Key.from_private_key_file(r"C:\Users\maity\.ssh\id_ed25519")
        self.gateway = paramiko.SSHClient()
        self.gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.gateway.connect(hostname="gw.cortexlab.fr", username="sayantan_maity", pkey=key)

        self.base_path = "/cortexlab/homes/sayantan_maity/cortexlab/jobs"


    def run_on_node(self, command):
        full_cmd = (
        "ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        f"-p 2222 root@{self.node_host} "
        f"{shlex.quote(command)}"
        )
        stdin, stdout, stderr = self.gateway.exec_command(full_cmd)

       
    

        ignore_patterns = [
        "Permanently added",
        "Warning:",
        "known hosts"
        ]
        clean_err = stderr.read().decode().strip()

            
        if clean_err:
            if not any(p in clean_err for p in ignore_patterns):

                raise Exception(clean_err)
        return stdout, stderr

    def get_node_info(self):

        hostname, _  = self.run_on_node("hostname")
        os_info, _ = self.run_on_node("cat /etc/os-release")
        hostname = hostname.read().decode()
        os_info = os_info.read().decode()
        return {
            "status": "ONLINE",
            "hostname": hostname,
            "os": os_info
        }

    
    
    def close(self):
        self.gateway.close()
    
