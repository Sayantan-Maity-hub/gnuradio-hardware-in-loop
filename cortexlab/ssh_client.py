import paramiko

class SSHConnection:
    def __init__(self, host):
        self.host=host.split(".")[0]
        self.gateway = paramiko.SSHClient()
        self.getway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.getway.connect(hostname="gw.cortexlab.fr", username="sayantan_maity")

        transport = self.gateway.get_transport()
        channel = transport.open_channel("direct-tcpip", (self.node_host, 2222), ("127.0.0.1", 0))
        
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=self.node_host, username="root", port=2222, sock=channel)


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
    