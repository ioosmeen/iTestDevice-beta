import paramiko
import time
import threading
from datetime import datetime

HOST = "192.168.1.100"
USERNAME = "root"
PASSWORD = "alpine"
RAM_ALERT_THRESHOLD = 100  # MB
SPECIAL_APPS = ["Cydia", "Sileo", "Zebra"]
LOG_FILE = "app.log"

stop_flag = False
command_flag = False
LANG = "EN"

MESSAGES = {
    "EN": {
        "welcome": "🔍 Monitoring started. Use '/killos' to kill apps, '/checkjb' whats your jailbreak '/lan' to change language.",
        "killos_prompt": "📋 Open apps:\n",
        "no_apps": "❌ No open apps found.",
        "invalid_choice": "❌ Invalid choice.",
        "cancelled": "Cancelled.",
        "kill_success": "🗡️ App killed: {app} (PID: {pid})",
        "kill_fail": "❌ Could not kill app: {app}, Error: {err}",
        "app_opened": "🚀 Opened: {app} — 🧠 RAM: {ram} MB — ⚙️ CPU: {cpu} %",
        "app_closed": "❌ Closed: {app}",
        "ram_warning": "⚠️ Warning: {app} is using {ram} MB RAM!",
        "special_app_alert": "🚨 Alert: Special app running → {app}",
        "monitoring_restart": "\n🔍 Monitoring resumed.\n",
        "killos_usage": "Use '/killos' to kill applications.",
        "language_changed_en": "Language changed to English.",
        "language_changed_tr": "Dil Türkçe olarak değiştirildi.",
        "command_prompt": "Enter command:",
        "connection_lost": "⚠️ SSH connection lost. Reconnecting...",
        "connection_failed": "❌ SSH connection failed. Retrying in 5 seconds...",
        "connection_success": "✅ SSH connected successfully.",
        "help_text": """
Available commands:
/killos    - Kill running apps.
/lan       - Switch language (English/Turkish).
/help      - Show this help message.
/restart   - Restart iPhone (user space reboot).
/exit      - Exit the program.
/battery   - Show battery status.
/checkjb   - Show jailbreak status.
/safe      - Enter Safe Mode.
""",
        "restarting": "🔄 Restarting iPhone...",
        "restart_success": "✅ Restart command sent successfully.",
        "restart_fail": "❌ Failed to restart: {err}",
        "jailbreak_detected": "🔓 Jailbreak detected! Type: {type}",
        "jailbreak_no": "🔒 No jailbreak detected.",
        "jailbreak_yes_rootless": "🔓 Jailbreak detected! Rootless jailbreak.",
        "jailbreak_yes_rootful": "🔓 Jailbreak detected! Rootful jailbreak.",
        "battery_status": "🔋 Battery Level: {level}% — State: {state}",
        "safe_mode_start": "🔧 Entering Safe Mode...",
        "safe_mode_success": "✅ Safe Mode command sent successfully.",
        "safe_mode_fail": "❌ Failed to enter Safe Mode: {err}",
    },
    "TR": {
        "welcome": "🔍 Takip başladı. Uygulamaları öldürmek için '/killos', dil değiştirmek için '/lan' yazın, jailbreakinizi öğrenmek için '/checkjb' yazın.",
        "killos_prompt": "📋 Açık uygulamalar:\n",
        "no_apps": "❌ Hiç açık uygulama bulunamadı.",
        "invalid_choice": "❌ Geçersiz seçim.",
        "cancelled": "İptal edildi.",
        "kill_success": "🗡️ Uygulama kapatıldı: {app} (PID: {pid})",
        "kill_fail": "❌ Uygulama kapatılamadı: {app}, Hata: {err}",
        "app_opened": "🚀 Açıldı: {app} — 🧠 RAM: {ram} MB — ⚙️ CPU: {cpu} %",
        "app_closed": "❌ Kapandı: {app}",
        "ram_warning": "⚠️ Uyarı: {app} {ram} MB RAM kullanıyor!",
        "special_app_alert": "🚨 Dikkat: Özel uygulama çalışıyor → {app}",
        "monitoring_restart": "\n🔍 Takip tekrar başladı.\n",
        "killos_usage": "Uygulamaları öldürmek için '/killos' komutunu kullanın.",
        "language_changed_en": "Language changed to English.",
        "language_changed_tr": "Dil Türkçe olarak değiştirildi.",
        "command_prompt": "Komut girin:",
        "connection_lost": "⚠️ SSH bağlantısı koptu. Yeniden bağlanıyor...",
        "connection_failed": "❌ SSH bağlantısı başarısız oldu. 5 saniye sonra tekrar denenecek...",
        "connection_success": "✅ SSH başarıyla bağlandı.",
        "help_text": """
Mevcut komutlar:
/killos    - Çalışan uygulamaları öldür.
/lan       - Dil değiştir (İngilizce/Türkçe).
/help      - Yardım mesajını göster.
/restart   - iPhone'u kullanıcı alanında yeniden başlat.
/exit      - Programdan çık.
/battery   - Pil durumunu göster.
/checkjb   - Jailbreak durumunu göster.
/safe      - Safe Mode'a geç.
""",
        "restarting": "🔄 iPhone yeniden başlatılıyor...",
        "restart_success": "✅ Yeniden başlatma komutu başarıyla gönderildi.",
        "restart_fail": "❌ Yeniden başlatma başarısız: {err}",
        "jailbreak_detected": "🔓 Jailbreak algılandı! Türü: {type}",
        "jailbreak_no": "🔒 Jailbreak algılanmadı.",
        "jailbreak_yes_rootless": "🔓 Jailbreak algılandı! Rootless jailbreak.",
        "jailbreak_yes_rootful": "🔓 Jailbreak algılandı! Rootful jailbreak.",
        "battery_status": "🔋 Pil Seviyesi: {level}% — Durum: {state}",
        "safe_mode_start": "🔧 Safe Mode'a geçiliyor...",
        "safe_mode_success": "✅ Safe Mode komutu başarıyla gönderildi.",
        "safe_mode_fail": "❌ Safe Mode'a geçiş başarısız: {err}",
    }
}

def msg(key, **kwargs):
    return MESSAGES[LANG][key].format(**kwargs)

def log_to_file(app_name, ram_mb):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{now},{app_name},{ram_mb} MB\n")

def kill_app(ssh, pid, app_name):
    try:
        ssh.exec_command(f"kill {pid}")
        print(msg("kill_success", app=app_name, pid=pid))
    except Exception as e:
        print(msg("kill_fail", app=app_name, err=e))

def create_ssh_client():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connected = False
    while not connected and not stop_flag:
        try:
            ssh_client.connect(HOST, username=USERNAME, password=PASSWORD)
            print(msg("connection_success"))
            connected = True
        except Exception:
            print(msg("connection_failed"))
            time.sleep(5)
    return ssh_client

def check_jailbreak(ssh):
    try:
        stdin, stdout, stderr = ssh.exec_command("test -e /var/jb && echo 'rootless' || (test -e /var/lib/dpkg/info && echo 'rootful' || echo 'none')")
        output = stdout.read().decode().strip()
        if output == "rootless":
            return "rootless"
        elif output == "rootful":
            return "rootful"
        else:
            return "none"
    except Exception:
        return "none"

def get_battery_status(ssh):
    try:
        stdin, stdout, stderr = ssh.exec_command("ioreg -c AppleSmartBattery -r -k CurrentCapacity -k MaxCapacity")
        output = stdout.read().decode()
        current_capacity = None
        max_capacity = None
        for line in output.splitlines():
            line = line.strip()
            if '"CurrentCapacity"' in line:
                parts = line.split(" = ")
                if len(parts) == 2:
                    current_capacity = int(parts[1])
            elif '"MaxCapacity"' in line:
                parts = line.split(" = ")
                if len(parts) == 2:
                    max_capacity = int(parts[1])
        if current_capacity is not None and max_capacity:
            level = round(current_capacity / max_capacity * 100)
        else:
            level = "Unknown"

        # Charging state
        stdin, stdout, stderr = ssh.exec_command("ioreg -n AppleSmartBattery -r -k IsCharging")
        output2 = stdout.read().decode()
        state = "Unknown"
        if "Yes" in output2:
            state = "Charging"
        elif "No" in output2:
            state = "Not Charging"
        return level, state
    except Exception:
        return "Unknown", "Unknown"

def monitor(ssh):
    seen_apps = {}
    global stop_flag, command_flag, LANG

    # Show jailbreak status on startup
    jb_type = check_jailbreak(ssh)
    if jb_type != "none":
        print(msg("jailbreak_detected", type=jb_type))
    else:
        print(msg("jailbreak_no"))

    print(msg("welcome") + "\n" + 
          ("/killos - Kill running apps, /restart - Restart your iPhone\n"
           if LANG == "EN" else
           "/killos - Çalışan uygulamaları öldür, /restart - iPhone'u yeniden başlat\n"))

    while not stop_flag:
        try:
            # Get currently running apps
            stdin, stdout, stderr = ssh.exec_command("ps aux | grep .app/")
            output = stdout.read().decode()

            current_apps = {}
            total_ram = 0

            # Parse process list lines to find apps
            for line in output.splitlines():
                if ".app/" in line:
                    parts = line.split()
                    try:
                        pid = int(parts[1])
                        mem_kb = int(parts[5])
                        mem_mb = round(mem_kb / 1024, 1)
                        cpu = parts[2]
                    except (IndexError, ValueError):
                        pid = None
                        mem_mb = "?"
                        cpu = "?"

                    app_path = next((p for p in parts if ".app/" in p), None)
                    if app_path:
                        app_name = app_path.split("/")[-1]

                        current_apps[app_name] = {"pid": pid, "ram": mem_mb, "cpu": cpu}
                        total_ram += mem_mb if isinstance(mem_mb, (int, float)) else 0

                        if app_name not in seen_apps:
                            print(msg("app_opened", app=app_name, ram=mem_mb, cpu=cpu))
                            log_to_file(app_name, mem_mb)

                            if mem_mb != "?" and mem_mb >= RAM_ALERT_THRESHOLD:
                                print(msg("ram_warning", app=app_name, ram=mem_mb))

                            if app_name in SPECIAL_APPS:
                                print(msg("special_app_alert", app=app_name))

            # Check closed apps
            closed_apps = set(seen_apps) - set(current_apps)
            for app_name in closed_apps:
                print(msg("app_closed", app=app_name))
                seen_apps.pop(app_name, None)

            seen_apps.update(current_apps)

            time.sleep(1)
        except Exception as e:
            print(f"Error during monitoring: {e}")
            time.sleep(2)

def command_loop(ssh):
    global stop_flag, command_flag, LANG

    while not stop_flag:
        try:
            if not command_flag:
                cmd = input(msg("command_prompt") + " ").strip()

                if cmd == "/killos":
                    command_flag = True
                    # List running apps
                    stdin, stdout, stderr = ssh.exec_command("ps aux | grep .app/")
                    output = stdout.read().decode()

                    apps = []
                    for line in output.splitlines():
                        if ".app/" in line:
                            parts = line.split()
                            try:
                                pid = int(parts[1])
                            except:
                                pid = None
                            app_path = next((p for p in parts if ".app/" in p), None)
                            if app_path:
                                app_name = app_path.split("/")[-1]
                                apps.append((app_name, pid))

                    if not apps:
                        print(msg("no_apps"))
                        command_flag = False
                        continue

                    print(msg("killos_prompt"))
                    for idx, (app_name, pid) in enumerate(apps, 1):
                        print(f"{idx}. {app_name} (PID: {pid})")
                    print("a. " + ("Kill all apps" if LANG == "EN" else "Tüm uygulamaları kapat"))
                    print("0. " + ("Cancel" if LANG == "EN" else "İptal"))

                    choice = input("Choice: ").strip().lower()
                    if choice == "0":
                        print(msg("cancelled"))
                    elif choice == "a":
                        # Kill all apps
                        for app_name, pid in apps:
                            kill_app(ssh, pid, app_name)
                    else:
                        try:
                            idx = int(choice) - 1
                            app_name, pid = apps[idx]
                            kill_app(ssh, pid, app_name)
                        except Exception:
                            print(msg("invalid_choice"))
                    command_flag = False

                elif cmd == "/lan":
                    # Change language
                    LANG = "TR" if LANG == "EN" else "EN"
                    if LANG == "EN":
                        print(msg("language_changed_en"))
                    else:
                        print(msg("language_changed_tr"))

                elif cmd == "/help":
                    print(msg("help_text"))

                elif cmd == "/restart":
                    print(msg("restarting"))
                    try:
                        ssh.exec_command("reboot")
                        print(msg("restart_success"))
                    except Exception as e:
                        print(msg("restart_fail", err=e))

                elif cmd == "/safe":
                    print(msg("safe_mode_start"))
                    try:
                        ssh.exec_command("killall -SEGV SpringBoard")
                        print(msg("safe_mode_success"))
                    except Exception as e:
                        print(msg("safe_mode_fail", err=e))

                elif cmd == "/exit":
                    stop_flag = True
                    print("Exiting...")
                    break

                elif cmd == "/battery":
                    level, state = get_battery_status(ssh)
                    print(msg("battery_status", level=level, state=state))

                elif cmd == "/checkjb":
                    jb_type = check_jailbreak(ssh)
                    if jb_type == "none":
                        print(msg("jailbreak_no"))
                    elif jb_type == "rootless":
                        print(msg("jailbreak_yes_rootless"))
                    elif jb_type == "rootful":
                        print(msg("jailbreak_yes_rootful"))

                else:
                    print(msg("help_text"))

            else:
                time.sleep(0.1)
        except KeyboardInterrupt:
            stop_flag = True
        except Exception as e:
            print(f"Command loop error: {e}")
            time.sleep(1)

def main():
    global stop_flag
    ssh = create_ssh_client()

    monitor_thread = threading.Thread(target=monitor, args=(ssh,))
    monitor_thread.daemon = True
    monitor_thread.start()

    command_loop(ssh)

    stop_flag = True
    ssh.close()

if __name__ == "__main__":
    main()
