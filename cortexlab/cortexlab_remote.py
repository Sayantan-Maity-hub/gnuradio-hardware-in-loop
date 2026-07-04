import paramiko
import config
import os
class cortexlab_Remote:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        username = config.USERNAME
        hostname = config.HOSTNAME
        key = paramiko.Ed25519Key.from_private_key_file(r"C:\Users\maity\.ssh\id_ed25519")
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
        
    def upload_folder(self, local_folder, remote_folder):
            sftp = self.ssh.open_sftp()
            parent_folder = remote_folder.split("/")[0]

            try:
                sftp.mkdir(parent_folder)
            except:
                pass
            try:
                 sftp.mkdir(remote_folder)
            except:
                 pass
            
            for filename in os.listdir(local_folder):
                local_path = os.path.join(local_folder, filename)
                remote_path = f"{remote_folder}/{filename}"

                if os.path.isfile(local_path):
                     sftp.put(local_path, remote_path)
            sftp.close()
        
    def close(self):
            self.ssh.close()

