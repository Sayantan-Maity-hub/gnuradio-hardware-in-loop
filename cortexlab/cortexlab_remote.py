import paramiko

class cortexlab_Remote:
    def __init__(self, hostname, username):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=hostname, username=username)

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
        
    def colse(self):
            self.ssh.close()
