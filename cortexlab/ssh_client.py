import paramiko

def get_node_info(host):
    ssh_host=(host.split(".")[0])
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ssh_host,
                username="root",
                port=2222,
                timeout=10
                )
    stdin, stdout, stderr =ssh.exec_command("hostname")
    hostname = stdout.read().decode().strip()

    _, stdout, _ = ssh.exec_command("cat /etc/os-release")
    os_info = stdout.read().decode()

    ssh.close()
    return {
        "status": "ONLINE",
        "hostname": hostname,
        "os": os_info
    }