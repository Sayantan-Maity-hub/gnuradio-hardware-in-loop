import paramiko
import os
import config
import time


class SSHConnection:
    def __init__(self, host):

        self.node_host = host.split(".")[0]
        if not self.node_host.startswith("m"):
            self.node_host = f"m{self.node_host}"

        self.gateway = paramiko.SSHClient()
        self.gateway.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("connecting to gateway....")

        key_file = os.getenv("HIL_PRIVATE_KEY")
        connect_args = {
            "hostname": config.HOSTNAME,
            "username": config.USERNAME,
            "timeout": 10,
            "banner_timeout": 10,
            "auth_timeout": 10,
        }

        if key_file:
            print(f"Using SSH key from: {key_file}")
            connect_args["pkey"] = paramiko.PKey.from_private_key_file(key_file)
            connect_args["look_for_keys"] = False
        else:
            print("Using default SSH keys")
            connect_args["look_for_keys"] = True

        print(connect_args)

        self.gateway.connect(**connect_args)
        print("gatway connected...")

        transport = self.gateway.get_transport()
        print("Authenticated to gateway:", transport.is_authenticated())
        self.channel = None

        for i in range(5):
            try:
                print(f"[{i+1}/5] Opening channel..")
                self.channel = transport.open_channel(
                    kind="direct-tcpip",
                    dest_addr=(self.node_host, 2222),
                    src_addr=("127.0.0.1", 0),
                )
                print("channel opened")
                break
            except Exception as e:
                print("Open channel failed: ", repr(e))
                if i == 4:
                    raise
                time.sleep(2)
        self.node = paramiko.SSHClient()
        self.node.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            print("Connecting to node...")
            node_transport = paramiko.Transport(self.channel)
            node_transport.start_client()

            node_transport.auth_none("root")
            if not node_transport.is_authenticated():
                raise paramiko.AuthenticationException(
                    "None authentication was rejected by the node"
                )
            self.node._transport = node_transport
            print("Node Connected")
        except Exception as e:
            print("Node connection failed")
            print(type(e).__name__)
            print(repr(e))
            self.close()
            raise

    def run_on_node(self, command):
        print("Running: ", command)

        stdin, stdout, stderr = self.node.exec_command(command)

        return stdout, stderr

    def get_node_info(self):

        hostname, _ = self.run_on_node("hostname")
        os_info, _ = self.run_on_node("cat /etc/os-release")
        hostname = hostname.read().decode()
        os_info = os_info.read().decode()
        return {"status": "ONLINE", "hostname": hostname, "os": os_info}

    def close(self):
        try:
            self.node.close()
        except Exception:
            pass
        try:
            if self.channel:
                self.channel.close()
        except Exception:
            pass
        try:
            self.gateway.close()
        except Exception:
            pass
