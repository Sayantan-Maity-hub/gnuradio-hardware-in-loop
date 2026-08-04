import paramiko
import config
import os


class cortexlab_Remote:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        username = config.USERNAME
        hostname = config.HOSTNAME
        key = paramiko.Ed25519Key.from_private_key_file(
            r"C:\Users\maity\.ssh\id_ed25519"
        )
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(hostname)
        print(username)

        self.ssh.connect(hostname=hostname, username=username, pkey=key)

    def run(self, command):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()

        if error:
            print(error)

        return output

    def upload_folder(self, local_path, remote_folder):
        print(local_path)
        print(remote_folder)
        self.run(f"mkdir -p '{remote_folder}'")
        sftp = self.ssh.open_sftp()

        if os.path.isfile(local_path):
            filename = os.path.basename(local_path)
            remote_path = f"{remote_folder}/{filename}"
            print("Uploading:", local_path, "-->", remote_path)
            sftp.put(local_path, remote_path)
        else:
            for filename in os.listdir(local_path):

                local_file = os.path.join(local_path, filename)

                print("LOCAL:", local_file)
                print("IS FILE:", os.path.isfile(local_file))

                if os.path.isfile(local_file):

                    remote_file = f"{remote_folder}/{filename}"

                    print(f"Uploading: {local_file}  {remote_file}")

                    try:
                        sftp.put(local_file, remote_file)
                        self.run(f"sed -i 's/\r$//' '{remote_file}'")
                        print("SUCCESS")
                    except Exception as e:
                        print("UPLOAD ERROR:", e)
        print(self.run(f"ls -l '{remote_folder}'"))
        sftp.close()

    def close(self):
        self.ssh.close()
