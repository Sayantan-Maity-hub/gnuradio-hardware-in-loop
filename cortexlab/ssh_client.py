import paramiko
import shlex

class SSHConnection:
    def __init__(self, host):
        self.node_host=host.split(".")[0]
        key = paramiko.Ed25519Key.from_private_key_file(r"C:\Users\maity\.ssh\id_ed25519")
        self.gateway = paramiko.SSHClient()
        self.gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.gateway.connect(hostname="gw.cortexlab.fr", username="sayantan_maity", pkey=key)

        self.key = key

    def run_on_node(self, command):
        full_cmd = (
        "ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        f"-p 2222 root@{self.node_host} "
        f"{shlex.quote(command)}"
        )
        stdin, stdout, stderr = self.gateway.exec_command(full_cmd)

        out = stdout.read().decode()
        err = stderr.read().decode()

        ignore_patterns = [
        "Permanently added",
        "Warning:",
        "known hosts"
        ]
        clean_err = err.strip()

            
        if clean_err:
            if not any(p in clean_err for p in ignore_patterns):

                raise Exception(err)
        return out

    def get_node_info(self):

        hostname = self.run_on_node("hostname")
        os_info = self.run_on_node("cat /etc/os-release")

        return {
            "status": "ONLINE",
            "hostname": hostname.strip(),
            "os": os_info
        }
    def upload_file(self, local_path, remote_path):
        stfp = self.gateway.open_sftp()
        stfp.put(local_path, remote_path)
        stfp.close()
        
    def close(self):
        self.gateway.close()
    