import os
import posixpath
import shlex
import paramiko
import config


class cortexlab_Remote:

    def __init__(self):
        self.ssh = paramiko.SSHClient()

        username = config.USERNAME
        hostname = config.HOSTNAME

        key = paramiko.Ed25519Key.from_private_key_file(
            r"C:\Users\maity\.ssh\id_ed25519"
        )

        self.ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )

        print(hostname)
        print(username)

        self.ssh.connect(
            hostname=hostname,
            username=username,
            pkey=key,
        )

    # Run remote command

    def run(self, command):

        stdin, stdout, stderr = self.ssh.exec_command(command)

        return stdout, stderr

    
    # Upload complete folder recursively
    

    def upload_folder(self, local_path, remote_folder,):
        """
        Upload complete local directory recursively.

        Example:

        local:

        21456/
        ├── node14/
        │   └── tx_chain.py
        ├── node15/
        │   └── rx_chain.py
        ├── node16/
        │   └── analysis.py
        └── parameters.json

        remote:

        3137/21456/
        ├── node14/
        │   └── tx_chain.py
        ├── node15/
        │   └── rx_chain.py
        ├── node16/
        │   └── analysis.py
        └── parameters.json
        """

        if not os.path.isdir(local_path):
            raise FileNotFoundError(
                f"Local folder not found: {local_path}"
            )

        print(
            f"Uploading folder:\n"
            f"  Local : {local_path}\n"
            f"  Remote: {remote_folder}"
        )

        sftp = self.ssh.open_sftp()

        try:

            
            # Create root remote directory
            

            self.run(
                f"mkdir -p {shlex.quote(remote_folder)}"
            )

            
            # Walk through complete directory tree
            

            for root, dirs, files in os.walk(
                local_path
            ):

                # Relative path from experiment root
                relative_dir = os.path.relpath(
                    root,
                    local_path,
                )

                # Root directory
                if relative_dir == ".":
                    remote_dir = remote_folder

                else:
                    remote_dir = posixpath.join(
                        remote_folder,
                        relative_dir.replace(
                            os.sep,
                            "/",
                        ),
                    )

                
                # Create remote directory
                

                self.run(
                    f"mkdir -p {shlex.quote(remote_dir)}"
                )

                
                # Upload every file
                

                for filename in files:

                    local_file = os.path.join(
                        root,
                        filename,
                    )

                    remote_file = posixpath.join(
                        remote_dir,
                        filename,
                    )

                    print(
                        f"Uploading:"
                        f"\n  {local_file}"
                        f"\n  -> {remote_file}"
                    )

                    try:

                        sftp.put(
                            local_file,
                            remote_file,
                        )

                        # Convert Windows CRLF to Unix LF
                        self.run(
                            "sed -i 's/\\r$//' "
                            f"{shlex.quote(remote_file)}"
                        )

                        print(
                            f"SUCCESS: {filename}"
                        )

                    except Exception as error:

                        print(
                            f"UPLOAD ERROR: "
                            f"{local_file}"
                        )

                        raise error

            print(
                f"\nExperiment folder "
                f"{local_path} uploaded successfully."
            )

        finally:
            sftp.close()

    
    # Download file
    

    def download_file(
        self,
        remote_file,
        local_file,
    ):

        sftp = self.ssh.open_sftp()

        try:

            local_dir = os.path.dirname(
                local_file
            )

            if local_dir:
                os.makedirs(
                    local_dir,
                    exist_ok=True,
                )

            print(
                f"Downloading:"
                f"\n  {remote_file}"
                f"\n  -> {local_file}"
            )

            sftp.get(
                remote_file,
                local_file,
            )

            print(
                "DOWNLOAD SUCCESS"
            )

        finally:
            sftp.close()

    
    # Close SSH connection
    

    def close(self):

        if self.ssh:
            self.ssh.close()