import paramiko

# SSH bilgilerini girin
HOST = "192.168.1.100"
USERNAME = "root"
PASSWORD = "alpine"

def respring_device():
    try:
        print("🔗 SSH bağlantısı kuruluyor...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USERNAME, password=PASSWORD)

        print("♻️ SpringBoard yeniden başlatılıyor (respring)...")
        ssh.exec_command("killall -9 SpringBoard")
        print("✅ Respring komutu başarıyla gönderildi.")

        ssh.close()

    except Exception as e:
        print(f"❌ Bağlantı veya komut hatası: {e}")

if __name__ == "__main__":
    respring_device()
