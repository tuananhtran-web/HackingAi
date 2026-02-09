import time
import sys
import random

def simulate_loading(text, duration=2):
    """Hiệu ứng loading giả lập"""
    sys.stdout.write(f"[*] {text}")
    sys.stdout.flush()
    for _ in range(duration):
        time.sleep(0.5)
        sys.stdout.write(".")
        sys.stdout.flush()
    print(" Done!")

def simulate_deauth_attack():
    print("\n[!!!] STARTING DEAUTH ATTACK SIMULATION [!!!]")
    print("[NOTE] Đây là chế độ GIẢ LẬP cho mục đích Demo/Testing.")
    print("       Không có gói tin tấn công thực sự nào được gửi đi.")
    
    target = input("\nNhập BSSID mục tiêu (hoặc Enter để auto): ").strip() or "AA:BB:CC:DD:EE:FF"
    interface = "wlan0mon"
    
    print(f"\n[*] Target locked: {target}")
    simulate_loading(f"Setting interface {interface} to monitor mode", 3)
    simulate_loading("Injecting DeAuth frames", 2)
    
    try:
        print("\n[+] Sending DeAuth to broadcast -- Press Ctrl+C to stop")
        packet_count = 0
        while True:
            packet_count += 1
            print(f"[{time.strftime('%H:%M:%S')}] Sending DeAuth to {target} -- seq={packet_count} -- ack=0")
            time.sleep(0.1)
            
            # Giả lập client ngắt kết nối ngẫu nhiên
            if packet_count % 15 == 0:
                client_mac = f"00:11:22:{random.randint(10,99)}:{random.randint(10,99)}:{random.randint(10,99)}"
                print(f"[*] Client [{client_mac}] disconnected from AP!")
            
            if packet_count > 100: # Tự dừng sau 100 gói cho demo
                break
                
    except KeyboardInterrupt:
        pass
    print("\n[!] Attack Simulation Stopped.")

def simulate_fake_ap():
    print("\n[!!!] STARTING FAKE AP SIMULATION [!!!]")
    print("[NOTE] Đây là chế độ GIẢ LẬP cho mục đích Demo/Testing.")
    
    ssid = input("\nNhập tên Wifi giả (SSID): ").strip() or "Free_Wifi_Airport"
    channel = input("Chọn kênh (Channel) [1-11]: ").strip() or "6"
    
    print(f"\n[*] Starting Fake AP: '{ssid}' on Channel {channel}")
    simulate_loading("Configuring DHCP Server")
    simulate_loading("Setting up DNS Spoofing")
    print(f"[*] AP '{ssid}' is now broadcasted!")
    
    try:
        print("\n[+] Waiting for victims... Press Ctrl+C to stop")
        while True:
            time.sleep(random.randint(2, 5))
            victim_ip = f"192.168.1.{random.randint(100, 200)}"
            victim_mac = f"AB:CD:EF:{random.randint(10,99)}:{random.randint(10,99)}:{random.randint(10,99)}"
            print(f"[*] New Client Connected: IP={victim_ip} MAC={victim_mac}")
            print(f"    -> DNS Request: google.com -> Spoofed to 192.168.1.1")
            
    except KeyboardInterrupt:
        pass
    print("\n[!] Fake AP Simulation Stopped.")

def simulate_wifi_crack():
    print("\n[!!!] STARTING WIFI CRACK SIMULATION [!!!]")
    print("[NOTE] Đây là chế độ GIẢ LẬP cho mục đích Demo/Testing.")
    
    target = input("\nNhập BSSID mục tiêu: ").strip() or "11:22:33:44:55:66"
    wordlist = "rockyou.txt"
    
    print(f"\n[*] Target: {target}")
    print(f"[*] Wordlist: {wordlist}")
    
    simulate_loading("Capturing WPA Handshake", 4)
    print(f"[+] WPA Handshake captured: {target}.cap")
    
    print("\n[*] Starting Dictionary Attack...")
    time.sleep(1)
    
    total_keys = 10000
    current = 0
    try:
        start_time = time.time()
        while current < total_keys:
            current += random.randint(100, 500)
            percent = min(100, (current / total_keys) * 100)
            elapsed = time.time() - start_time
            speed = int(current / (elapsed + 0.01))
            
            sys.stdout.write(f"\r[>] Testing keys: {current}/{total_keys} ({percent:.2f}%) -- Speed: {speed} k/s")
            sys.stdout.flush()
            time.sleep(0.1)
            
            # Giả lập tìm thấy pass
            if current > 8000:
                print(f"\n\n[+] KEY FOUND! [ PASS: password123 ]")
                print("[*] Decrypting traffic...")
                return

    except KeyboardInterrupt:
        pass
    print("\n[!] Crack Simulation Stopped.")
