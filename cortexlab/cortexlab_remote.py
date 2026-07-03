import paramiko
import config
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
            try:
                sftp.mkdir(remote_folder)
            except:
                pass
            sftp.put(f"{local_folder}/scenario.yaml", f"{remote_folder}/scenario.yaml")
            sftp.close()
        
    def close(self):
            self.ssh.close()

