import paramiko
import socket
from datetime import datetime

# SSH Bağlantı bilgileri
HOST = "192.168.1.184"
PORT = 22
USERNAME = "root"
PASSWORD = "alpine"

def create_log_on_remote():
    # SSH Client oluştur
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD)
        print("SSH CONNETED SUCESSFUL")

        # PC adını al
        pc_name = socket.gethostname()

        # Tarihi al
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Uzaktaki klasör ve dosya yolu
        remote_dir = f"/var/{pc_name}"
        remote_file = f"{remote_dir}/.connected.log"

        # Komutları sırayla çalıştır
        commands = [
            f"mkdir -p {remote_dir}",
            f"echo 'Connected at {now} from {pc_name}' >> {remote_file}"
        ]

        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            error = stderr.read().decode()
            if error:
                print(f"Hata: {error}")

        print(f"Log File {remote_file} Created.")
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    create_log_on_remote()
