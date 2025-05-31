import paramiko
import os
from datetime import datetime
from pathlib import Path
import stat

HOST = "192.168.1.196"
USERNAME = "root"
PASSWORD = "alpine"

def create_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USERNAME, password=PASSWORD)
    return ssh

def list_apps_from_multiple_paths(ssh):
    paths = [
        "/var/containers/Bundle/Application",
        "/Applications",
        "/System/Library/CoreServices"
    ]
    apps = []
    for base_path in paths:
        # Sadece klasörleri ara, dosyalar olmasın
        cmd = f"find {base_path} -maxdepth 3 -type d -name '*.app' 2>/dev/null"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode().splitlines()
        apps.extend(result)
    return apps

def list_running_apps(ssh):
    # Çalışan uygulamaları bul
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep .app/")
    output = stdout.read().decode()
    running_apps = {}

    for line in output.splitlines():
        if ".app/" in line:
            parts = line.split()
            app_path = next((p for p in parts if ".app/" in p), None)
            if app_path:
                # Burada app_path'nin sonu mutlaka .app ile bitmeli
                # Eğer bitmiyorsa yolun üst dizinine çıkabiliriz:
                if not app_path.endswith(".app"):
                    app_path = app_path.split(".app")[0] + ".app"
                app_name = os.path.basename(app_path).replace(".app", "")
                running_apps[app_name] = app_path

    all_apps_list = list_apps_from_multiple_paths(ssh)

    all_apps = {}

    for app_name, path in running_apps.items():
        all_apps[app_name] = path

    for path in all_apps_list:
        app_name = os.path.basename(path).replace(".app", "")
        if app_name not in all_apps:
            all_apps[app_name] = path

    return all_apps

def sftp_download_dir(sftp, remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    for item in sftp.listdir_attr(remote_dir):
        remote_path = remote_dir + '/' + item.filename
        local_path = os.path.join(local_dir, item.filename)
        if stat.S_ISDIR(item.st_mode):
            sftp_download_dir(sftp, remote_path, local_path)
        else:
            sftp.get(remote_path, local_path)

def dump_app_bundle(ssh, app_name, bundle_path):
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
    print("dumped")

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
                print("❌ No apps found.")
                continue

            print("📋 Available apps:")
            app_names = list(apps.keys())
            for i, app_name in enumerate(app_names, 1):
                print(f"{i}. {app_name}")
            choice = input("Select an app to dump: ").strip()

            try:
                idx = int(choice) - 1
                if idx < 0 or idx >= len(app_names):
                    raise ValueError("Invalid index")
                app_name = app_names[idx]
                bundle_path = apps[app_name]
                dump_app_bundle(ssh, app_name, bundle_path)
            except Exception as e:
                print(f"❌ Invalid selection or error: {e}")
        else:
            print("❌ Unknown command.")

if __name__ == "__main__":
    main()
