import paramiko
import os
import time
from datetime import datetime
from pathlib import Path
import stat  # Eklendi: dizin kontrolü için

HOST = "192.168.1.196"
USERNAME = "root"
PASSWORD = "alpine"

def create_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USERNAME, password=PASSWORD)
    return ssh

def list_running_apps(ssh):
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep .app/")
    output = stdout.read().decode()
    apps = {}

    for line in output.splitlines():
        if ".app/" in line:
            parts = line.split()
            pid = parts[1]
            app_path = next((p for p in parts if ".app/" in p), None)
            if app_path:
                app_name = os.path.basename(app_path).replace(".app", "")
                apps[app_name] = app_path
    return apps

def find_bundle_path(ssh, app_name):
    cmd = f"find /var/containers/Bundle/Application -name '{app_name}.app' | head -n 1"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read().decode().strip()
    # Burada artık .app klasörünün tam yolu döndürülüyor
    return result if result else None

def sftp_download_dir(sftp, remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    for item in sftp.listdir_attr(remote_dir):
        remote_path = remote_dir + '/' + item.filename
        local_path = os.path.join(local_dir, item.filename)
        if stat.S_ISDIR(item.st_mode):  # stat modülü ile dizin kontrolü
            sftp_download_dir(sftp, remote_path, local_path)
        else:
            sftp.get(remote_path, local_path)

def dump_app_bundle(ssh, app_name):
    bundle_path = find_bundle_path(ssh, app_name)
    if not bundle_path:
        print(f"❌ Couldn't find bundle path for {app_name}")
        return

    desktop = str(Path.home() / "Desktop")
    dump_dir_name = f".dump-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{HOST}"
    local_dump_path = os.path.join(desktop, dump_dir_name, app_name)
    print(f"📦 Dumping {app_name} from {bundle_path} to {local_dump_path}...")

    sftp = ssh.open_sftp()
    sftp_download_dir(sftp, bundle_path, local_dump_path)
    sftp.close()

    print(f"✅ Dump complete! Saved at:\n{local_dump_path}")
    print("dumped")  # Burada dumped yazısı eklendi

def main():
    ssh = create_ssh_client()
    print(f"✅ Connected to {HOST}")

    while True:
        cmd = input("Enter command (/dump or /exit): ").strip().lower()
        if cmd == "/exit":
            break
        elif cmd == "/dump":
            apps = list_running_apps(ssh)
            if not apps:
                print("❌ No running apps found.")
                continue

            print("📋 Running apps:")
            for i, app_name in enumerate(apps.keys(), 1):
                print(f"{i}. {app_name}")
            choice = input("Select an app to dump: ").strip()

            try:
                idx = int(choice) - 1
                app_name = list(apps.keys())[idx]
                dump_app_bundle(ssh, app_name)
            except:
                print("❌ Invalid selection.")
        else:
            print("❌ Unknown command.")

if __name__ == "__main__":
    main()
