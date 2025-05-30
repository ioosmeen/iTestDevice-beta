import paramiko
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime

HOST = "192.168.1.184"
PORT = 22
USERNAME = "root"
PASSWORD = "alpine"

def check_jailbreak(ssh):
    try:
        stdin, stdout, stderr = ssh.exec_command(
            "test -e /var/jb && echo 'rootless' || (test -e /var/lib/dpkg/info && echo 'rootful' || echo 'none')")
        output = stdout.read().decode().strip()
        return output
    except Exception:
        return "none"

def sftp_upload(ssh, local_path, remote_dir, jb_type):
    sftp = ssh.open_sftp()
    try:
        # Restrict writing to system directories if rootless jailbreak
        restricted_dirs_rootless = ["/var", "/usr", "/etc", "/bin", "/sbin"]
        if jb_type == "rootless":
            for restricted in restricted_dirs_rootless:
                if remote_dir.startswith(restricted):
                    messagebox.showerror("Error", f"You cannot write to '{restricted}' directory on rootless jailbreak.")
                    return

        # Check if remote directory exists, create if not
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            try:
                sftp.mkdir(remote_dir)
            except Exception as e:
                messagebox.showwarning("Warning", f"Could not create target directory: {e}")

        if os.path.isfile(local_path):
            filename = os.path.basename(local_path)
            remote_path = remote_dir.rstrip('/') + '/' + filename
            sftp.put(local_path, remote_path)
            messagebox.showinfo("Success", f"File uploaded to:\n{remote_path}")

        elif os.path.isdir(local_path):
            # Upload folder contents (only first level)
            for root, dirs, files in os.walk(local_path):
                relative_path = os.path.relpath(root, local_path)
                target_dir = remote_dir
                if relative_path != '.':
                    target_dir = remote_dir.rstrip('/') + '/' + relative_path.replace('\\', '/')
                    try:
                        sftp.mkdir(target_dir)
                    except Exception:
                        pass
                for file in files:
                    local_file = os.path.join(root, file)
                    remote_file = target_dir.rstrip('/') + '/' + file
                    sftp.put(local_file, remote_file)
            messagebox.showinfo("Success", "Folder contents uploaded.")
        else:
            messagebox.showerror("Error", "Invalid file or folder selected.")
    finally:
        sftp.close()

def main():
    # SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD)
    except Exception as e:
        print(f"Failed to connect via SSH: {e}")
        return

    jb_type = check_jailbreak(ssh)
    print(f"Jailbreak type: {jb_type}")

    root = tk.Tk()
    root.withdraw()  # Hide main window

    while True:
        choice = messagebox.askquestion("File or Folder?", "Are you uploading a file?\nIf No, a folder will be selected.")
        if choice == 'yes':
            local_path = filedialog.askopenfilename(title="Select a file")
        else:
            local_path = filedialog.askdirectory(title="Select a folder")

        if not local_path:
            if messagebox.askyesno("Exit", "No file/folder selected. Do you want to exit?"):
                ssh.close()
                return
            else:
                continue

        remote_dir = simpledialog.askstring("Target Directory", "Enter the target directory on the iPhone (e.g. /var/mobile/Documents):")
        if not remote_dir:
            messagebox.showwarning("Warning", "Target directory cannot be empty.")
            continue

        sftp_upload(ssh, local_path, remote_dir, jb_type)

        if not messagebox.askyesno("Continue", "Do you want to upload another file/folder?"):
            break

    ssh.close()

if __name__ == "__main__":
    main()
