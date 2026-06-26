import paramiko

class SSHConnection:
    def __init__(self, host):
        self.host=host.split(".")[0]
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=self.host, username="root", port=2222, timeout=10)


    def get_node_info(self):
    
        stdin, stdout, stderr =self.exec_command("hostname")
        hostname = stdout.read().decode().strip()

        _, stdout, _ = self.exec_command("cat /etc/os-release")
        os_info = stdout.read().decode()

        return {
            "status": "ONLINE",
            "hostname": hostname,
            "os": os_info
        }
    def close(self):
        self.ssh.close()
    