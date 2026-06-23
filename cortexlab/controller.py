import paramiko


def get_node_info(hostname, username="root", port=2222):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    ssh.connect(
        hostname=hostname,
        username=username,
        port=port
    )
    stdin, stdout, stderr = ssh.exec_command("hostname")

    node_hostname = stdout.read().decode().strip()
