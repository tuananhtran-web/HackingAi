import socket
import requests
import subprocess
import re
import platform
import os
import shutil
from urllib.parse import urlparse, quote
import threading
import webbrowser
import json
import sys

def is_termux() -> bool:
    """Kiểm tra xem script có đang chạy trên Termux (Android) hay không."""
    return "com.termux" in os.environ.get("PREFIX", "")

def check_and_install_termux_dependencies():
    """
    Tự động kiểm tra và đề xuất cài đặt các gói cần thiết trên Termux.
    """
    if not is_termux():
        return

    required_packages = {
        "termux-wifi-scaninfo": "termux-api",
        "termux-open-url": "termux-api",
        "traceroute": "tracepath", # traceroute thường nằm trong package tracepath hoặc inetutils
        "nslookup": "dnsutils"
    }
    
    missing_packages = set()
    
    print("[*] Termux Environment: Đang kiểm tra các công cụ hỗ trợ...")
    
    for command, package in required_packages.items():
        if shutil.which(command) is None:
            # Special case for traceroute which might be installed but named differently or in different package
            if command == "traceroute":
                # Check alternatives
                if shutil.which("tracepath") is None:
                     missing_packages.add("tracepath") # Suggest installing tracepath
            else:
                missing_packages.add(package)
            
    if missing_packages:
        print(f"\n[!] CẢNH BÁO: Phát hiện thiếu các gói hỗ trợ Termux: {', '.join(missing_packages)}")
        print("    Các tính năng như quét WiFi, tìm đường, hoặc traceroute có thể không hoạt động.")
        
        while True:
            choice = input(f"    Bạn có muốn tự động cài đặt chúng ngay bây giờ? (y/n): ").strip().lower()
            if choice in ['y', 'yes', 'ok']:
                packages_str = " ".join(missing_packages)
                print(f"[*] Đang chạy lệnh: pkg install {packages_str} -y")
                try:
                    subprocess.run(f"pkg install {packages_str} -y", shell=True, check=True)
                    print("[+] Cài đặt hoàn tất! Vui lòng khởi động lại ứng dụng nếu cần.")
                    
                    # Nếu cài termux-api, nhắc user cài app
                    if "termux-api" in missing_packages:
                         print("\n[IMPORTANT] Bạn vừa cài gói 'termux-api'.")
                         print("Hãy đảm bảo bạn ĐÃ CÀI ĐẶT ỨNG DỤNG 'Termux:API' từ Google Play/F-Droid")
                         print("Và cấp quyền VỊ TRÍ (Location) cho ứng dụng đó để quét WiFi.")
                         input("    Nhấn Enter để tiếp tục...")
                except Exception as e:
                    print(f"[-] Lỗi khi cài đặt: {e}")
                    print("    Bạn vui lòng thử cài thủ công bằng lệnh: pkg install <tên_gói>")
                break
            elif choice in ['n', 'no']:
                print("    Đã bỏ qua cài đặt. Một số tính năng sẽ bị hạn chế.")
                break
    else:
        print("[+] Termux Environment: Đủ công cụ.")

def scan_target(target: str, ports: list = None) -> dict:
    """
    Quét các cổng mở trên mục tiêu (IP hoặc domain).
    Hữu ích để xác định các dịch vụ đang chạy.
    
    Args:
        target: Địa chỉ IP hoặc tên miền cần quét.
        ports: Danh sách các cổng cần quét. Nếu không cung cấp, sẽ quét các cổng phổ biến.
    """
    if ports is None:
        ports = [80, 443, 8080, 8443, 21, 22, 23, 25, 53, 110, 143, 3306, 3389, 554, 37777]
        
    results = {}
    print(f"[*] System: Đang quét mục tiêu: {target} trên các cổng {ports}...")
    
    # Resolve domain to IP if needed
    try:
        ip = socket.gethostbyname(target)
        results['target'] = target
        results['ip'] = ip
    except socket.gaierror:
        return {"error": f"Không thể phân giải tên miền: {target}"}

    open_ports = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5) # Timeout ngắn để quét nhanh hơn
            result = sock.connect_ex((ip, port))
            if result == 0:
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                open_ports.append({"port": port, "service": service})
            sock.close()
        except Exception:
            pass
    
    results['open_ports'] = open_ports
    if not open_ports:
        results['message'] = "Không tìm thấy cổng mở nào trong danh sách quét."
    
    return results

def check_http_security_headers(url: str) -> dict:
    """
    Kiểm tra các HTTP security headers của một URL để đánh giá cấu hình bảo mật web cơ bản.
    
    Args:
        url: Đường dẫn URL cần kiểm tra (ví dụ: google.com hoặc http://example.com)
    """
    if not url.startswith("http"):
        url = "http://" + url
    
    print(f"[*] System: Đang kiểm tra HTTP Headers cho: {url}...")
        
    try:
        response = requests.get(url, timeout=5)
        headers = response.headers
        
        # Các header bảo mật quan trọng cần kiểm tra
        security_headers_check = {
            "X-Frame-Options": "Chống Clickjacking",
            "X-Content-Type-Options": "Chống MIME Sniffing",
            "Strict-Transport-Security": "Bắt buộc HTTPS (HSTS)",
            "Content-Security-Policy": "Chống XSS và Injection (CSP)",
            "X-XSS-Protection": "Bộ lọc XSS của trình duyệt (Cũ)",
            "Referrer-Policy": "Kiểm soát thông tin Referrer",
            "Permissions-Policy": "Kiểm soát tính năng trình duyệt"
        }
        
        found_headers = {}
        missing_headers = []
        
        for header, description in security_headers_check.items():
            if header in headers:
                found_headers[header] = headers[header]
            else:
                missing_headers.append(f"{header} ({description})")
                
        return {
            "url": url,
            "status_code": response.status_code,
            "found_security_headers": found_headers,
            "missing_security_headers": missing_headers
        }
    except Exception as e:
        return {"error": f"Không thể kết nối đến URL: {str(e)}"}

def get_my_ip() -> dict:
    """Lấy địa chỉ IP public của máy hiện tại."""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def scan_local_network() -> dict:
    """
    Quét mạng nội bộ (LAN) để tìm các thiết bị đang kết nối.
    Sử dụng lệnh ARP để liệt kê các thiết bị trong cache.
    Hỗ trợ phát hiện IP Camera cơ bản dựa trên MAC Address hoặc Port Scan nhanh.
    Hỗ trợ cả Windows và Linux/Termux.
    """
    print("[*] System: Đang quét mạng nội bộ (ARP Scan)...")
    devices = []
    
    try:
        # Sử dụng lệnh arp -a để lấy danh sách thiết bị
        # Trên Android 10+, /proc/net/arp bị chặn, arp -a có thể trả về rỗng hoặc permission denied
        cmd = "arp -a"
        
        # Nếu là Termux/Linux, thử dùng ip neighbor nếu arp thất bại hoặc trả về ít
        if is_termux() or platform.system() == "Linux":
            cmd = "arp -a || ip neighbor"
            
        output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
        
        # Regex đa năng hỗ trợ cả Windows và Linux/Termux
        # Windows: 192.168.1.1 ... 00-11-22-33-44-55
        # Linux/Termux: ? (192.168.1.1) at 00:11:22:33:44:55 ...
        # ip neighbor: 192.168.1.1 dev wlan0 lladdr 00:11:22:33:44:55 REACHABLE
        
        # Pattern 1: Bắt IP
        ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        # Pattern 2: Bắt MAC (hỗ trợ cả dấu : và -)
        mac_pattern = r'([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})'
        
        for line in output.splitlines():
            ip_match = re.search(ip_pattern, line)
            mac_match = re.search(mac_pattern, line)
            
            if ip_match and mac_match:
                ip = ip_match.group(1)
                mac = mac_match.group(1)
                
                # Loại bỏ IP Multicast/Broadcast/Loopback
                if ip.startswith("224.") or ip.endswith(".255") or ip == "127.0.0.1":
                    continue
                    
                device_info = {"ip": ip, "mac": mac, "type": "Unknown"}
                if device_info not in devices:
                    devices.append(device_info)
            
    except Exception as e:
        return {"error": f"Lỗi khi quét ARP: {str(e)}"}

    if not devices:
        msg = "Không tìm thấy thiết bị nào (hoặc cache ARP trống). Hãy thử ping một vài IP hoặc dùng scan_for_cameras để quét chủ động."
        if is_termux():
            msg += " Lưu ý: Trên Android 10+, quyền truy cập ARP bị hạn chế. Bạn có thể cần Root hoặc chỉ quét được thiết bị đã giao tiếp."
        return {"message": msg}
        
    return {"devices": devices, "count": len(devices), "note": "Để phát hiện nhiều thiết bị hơn, hãy thực hiện ping sweep thủ công hoặc truy cập các thiết bị."}

def scan_for_cameras(network_prefix: str = None) -> dict:
    """
    Tìm kiếm IP Camera trong mạng nội bộ bằng cách quét các cổng RTSP (554) và Web (80, 8080).
    
    Args:
        network_prefix: Tiền tố mạng (ví dụ: '192.168.1.'). Nếu không có, sẽ cố gắng đoán từ IP máy.
    """
    print("[*] System: Đang tìm kiếm IP Camera trong mạng...")
    
    if not network_prefix:
        # Lấy IP LAN hiện tại để đoán prefix
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            network_prefix = ".".join(local_ip.split(".")[:-1]) + "."
        except:
            return {"error": "Không thể xác định mạng LAN hiện tại."}

    cameras = []
    
    def check_camera(ip):
        # Các cổng phổ biến của Camera: 554 (RTSP), 80 (Web), 8080 (Web), 37777 (Dahua), 8000 (Hikvision)
        cam_ports = [554, 80, 8080, 37777, 8000]
        try:
            for port in cam_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.2)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:
                    cameras.append({"ip": ip, "port": port, "service": "Possible Camera Stream/Web"})
                    return # Tìm thấy 1 cổng là đủ nghi ngờ
        except:
            pass

    threads = []
    # Quét nhanh 254 host trong subnet
    print(f"[*] System: Đang quét subnet {network_prefix}0/24...")
    for i in range(1, 255):
        ip = f"{network_prefix}{i}"
        t = threading.Thread(target=check_camera, args=(ip,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    return {"found_cameras": cameras, "count": len(cameras)}

def analyze_website_health(url: str) -> dict:
    """
    Phân tích sức khỏe và bảo mật cơ bản của Website (Passive Audit).
    Kiểm tra robots.txt, sitemap.xml và nhận diện công nghệ cơ bản.
    
    Args:
        url: URL của website.
    """
    if not url.startswith("http"):
        url = "http://" + url
        
    print(f"[*] System: Đang phân tích website: {url}...")
    results = {"url": url}
    
    try:
        # Check robots.txt
        robots_url = url.rstrip('/') + "/robots.txt"
        resp = requests.get(robots_url, timeout=5)
        if resp.status_code == 200:
            results["robots_txt"] = "Found (200 OK)"
            # Phân tích nội dung robots.txt để tìm đường dẫn nhạy cảm
            sensitive_paths = [line for line in resp.text.splitlines() if "Disallow:" in line and ("admin" in line or "login" in line or "backup" in line)]
            if sensitive_paths:
                results["robots_sensitive_entries"] = sensitive_paths
        else:
            results["robots_txt"] = f"Not Found ({resp.status_code})"
            
        # Check Server Header
        main_resp = requests.get(url, timeout=5)
        results["server_header"] = main_resp.headers.get("Server", "Unknown")
        results["powered_by"] = main_resp.headers.get("X-Powered-By", "Unknown")
        
    except Exception as e:
        results["error"] = str(e)
        
    return results

def request_termux_permissions():
    """
    Yêu cầu cấp quyền trên Termux (Storage, Location, etc.)
    """
    if not is_termux():
        return

    print("\n[*] Termux Permission Manager")
    print("    Tool cần một số quyền để hoạt động chính xác.")
    
    # 1. Storage Permission
    print("1. Yêu cầu quyền truy cập bộ nhớ (Storage) để lưu log/kết quả...")
    try:
        # termux-setup-storage sẽ kích hoạt popup xin quyền của Android
        subprocess.run(["termux-setup-storage"], check=False)
        print("    [+] Đã gửi lệnh yêu cầu. Hãy nhấn 'Allow/Cho phép' trên màn hình nếu có popup.")
    except FileNotFoundError:
        print("    [!] Không tìm thấy lệnh 'termux-setup-storage'.")

    # 2. Location Permission (cho WiFi Scan)
    print("\n2. Yêu cầu quyền Vị Trí (Location) cho tính năng Quét WiFi...")
    print("    [WARNING] Android yêu cầu quyền Vị trí để quét được WiFi xung quanh.")
    print("    Bạn cần cấp quyền này cho ứng dụng **Termux:API** (không phải Termux thường).")
    
    choice = input("    Bạn có muốn mở cài đặt để cấp quyền ngay không? (y/n): ").strip().lower()
    if choice in ['y', 'yes']:
        # Thử mở cài đặt ứng dụng (cần termux-open)
        try:
            # Mở trang Settings của Termux:API (nếu có thể, hoặc mở Settings chung)
            # Android không cho mở trực tiếp trang permission của app khác dễ dàng qua cmd
            print("    Đang mở cài đặt WiFi/Location...")
            subprocess.run(["termux-open-url", "package:com.termux.api"], check=False) 
        except:
            print("    [!] Không thể mở cài đặt tự động. Vui lòng mở thủ công.")

    print("    -> Hướng dẫn thủ công: Settings > Apps > Termux:API > Permissions > Location > Allow All the time.")

APP_PACKAGES = {
    "facebook": "com.facebook.katana",
    "messenger": "com.facebook.orca",
    "youtube": "com.google.android.youtube",
    "tiktok": "com.ss.android.ugc.trill",
    "zalo": "com.zing.zalo",
    "chrome": "com.android.chrome",
    "gmail": "com.google.android.gm",
    "maps": "com.google.android.apps.maps",
    "settings": "com.android.settings",
    "camera": "com.sec.android.app.camera", # Samsung
    "spotify": "com.spotify.music",
    "termux": "com.termux",
    "bravigo": "com.bravigo.dvr.vietmap", # Ví dụ đoán tên package, user có thể cần cung cấp chính xác
}

def launch_app(app_name: str) -> dict:
    """
    Mở ứng dụng trên thiết bị Android (Termux).
    Sử dụng tên ứng dụng phổ biến (facebook, youtube...) hoặc tên gói (package name).
    Ví dụ: 'mở app facebook', 'launch youtube', 'com.zing.zalo'
    """
    if not is_termux():
        return {"error": "Tính năng mở App chỉ hỗ trợ trên Android Termux."}

    app_name_lower = app_name.lower().strip()
    package_name = APP_PACKAGES.get(app_name_lower, app_name_lower)
    
    print(f"[*] System: Đang thử mở ứng dụng: {app_name} ({package_name})...")
    
    try:
        # Cách 1: Dùng lệnh monkey (Hack để launch app không cần root)
        # monkey -p <package> 1: Giả lập 1 thao tác user vào app -> App sẽ mở lên
        cmd = f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        
        # Suppress output ồn ào của monkey
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "success", "message": f"Đã gửi lệnh mở App {app_name} ({package_name})."}
        
    except subprocess.CalledProcessError:
        # Cách 2: Nếu monkey thất bại (do sai package name), thử termux-open với scheme
        # Ví dụ: fb:// cho facebook (nhưng không phải app nào cũng có scheme chuẩn)
        return {"error": f"Không thể mở app '{app_name}'. Có thể sai tên gói (Package Name) hoặc app chưa cài đặt.\n    Gợi ý: Hãy nhập đúng Package Name (ví dụ: com.facebook.katana)."}
    except Exception as e:
        return {"error": f"Lỗi không xác định khi mở app: {str(e)}"}

def scan_wifi_networks():
    """
    Quét các mạng WiFi xung quanh và đánh giá độ an toàn (Audit).
    """
    print("[*] System: Đang quét mạng WiFi xung quanh...")
    
    networks = []
    
    # Hỗ trợ Android Termux
    if is_termux():
        print("[*] Phát hiện môi trường Termux. Đang thử dùng 'termux-wifi-scaninfo'...")
        print("    [TIP] Hãy chắc chắn bạn đã BẬT VỊ TRÍ (GPS) và cấp quyền Location cho Termux:API.")
        
        try:
            # Giảm timeout xuống 8s để đỡ phải chờ lâu nếu treo
            result = subprocess.run(['termux-wifi-scaninfo'], capture_output=True, text=True, timeout=8)
            if result.returncode == 0:
                wifi_info = json.loads(result.stdout)
                # termux-wifi-scaninfo trả về list các dict
                for wifi in wifi_info:
                    ssid = wifi.get('ssid', 'Hidden')
                    # Phân tích bảo mật cơ bản
                    security_note = "Unknown"
                    # Termux API đôi khi không trả về security type rõ ràng trong scaninfo cũ
                    # Nhưng ta có thể đoán hoặc giả lập phân tích cho demo
                    
                    networks.append({
                        "ssid": ssid,
                        "bssid": wifi.get('bssid', ''),
                        "signal": wifi.get('rssi', 0),
                        "frequency": wifi.get('frequency', 0),
                        "info": "Termux Scan"
                    })
                
                # Format output cho đẹp và đánh giá rủi ro
                formatted_output = "\n--- KẾT QUẢ QUÉT WIFI (AUDIT) ---\n"
                formatted_output += f"{'SSID':<25} | {'SIGNAL':<8} | {'STATUS'}\n"
                formatted_output += "-"*60 + "\n"
                
                for net in networks:
                    ssid = net['ssid']
                    signal = net['signal']
                    # Giả lập đánh giá (vì API hạn chế)
                    status = "Detected"
                    if "Free" in ssid or "Open" in ssid or "Guest" in ssid:
                        status = "[!] RISKY (Có thể không mật khẩu)"
                    
                    formatted_output += f"{ssid:<25} | {signal:<8} | {status}\n"
                
                return {"networks": networks, "display": formatted_output}
            else:
                # Nếu lỗi, có thể do chưa cấp quyền
                request_termux_permissions()
                return {"error": f"Lỗi termux-wifi-scaninfo: {result.stderr}. Đã thử yêu cầu quyền."}
        except subprocess.TimeoutExpired:
            return {"error": "Lệnh 'termux-wifi-scaninfo' bị treo (Timeout). Hãy kiểm tra GPS."}
        except FileNotFoundError:
            return {"error": "Thiếu 'termux-wifi-scaninfo'. Chạy: pkg install termux-api"}
        except Exception as e:
            return {"error": f"Lỗi không xác định: {str(e)}"}

    # Mặc định chạy lệnh Windows netsh
    try:
        # ... (giữ nguyên code Windows cũ nếu cần, hoặc focus vào Termux theo context user)
        output = subprocess.check_output("netsh wlan show networks mode=bssid", shell=True).decode('utf-8', errors='ignore')
        return {"raw_output": output}
    except Exception as e:
        return {"error": str(e)}

def run_system_command(command: str) -> dict:
    """
    Thực hiện các lệnh hệ thống (CLI) linh hoạt để mở rộng khả năng của AI.
    Cho phép AI tự do sáng tạo cách sử dụng lệnh để đạt mục tiêu (ví dụ: ping, nslookup, tracert, curl, whois).
    CẢNH BÁO: Chỉ sử dụng cho các lệnh thu thập thông tin và kiểm thử an toàn.
    """
    print(f"[*] System: Đang thực thi lệnh hệ thống: {command}...")
    
    # Danh sách đen các từ khóa nguy hiểm để ngăn chặn phá hoại
    dangerous_keywords = [
        "del ", "rm ", "format ", "shutdown", "restart", "reboot", 
        "net user", "net localgroup", "reg add", "reg delete",
        ">", ">>", "|", # Chặn chuyển hướng và pipe để tránh command injection phức tạp
        "powershell", "cmd.exe" # Hạn chế gọi shell con
    ]
    
    # Kiểm tra an toàn cơ bản
    lower_cmd = command.lower()
    for keyword in dangerous_keywords:
        if keyword in lower_cmd:
            return {"error": f"Lệnh bị từ chối vì chứa từ khóa nguy hiểm hoặc không được phép: '{keyword}'"}

    try:
        # Chạy lệnh và lấy output
        # timeout=30s để tránh treo
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=30).decode('utf-8', errors='ignore')
        return {"command": command, "output": output}
    except subprocess.TimeoutExpired:
        return {"error": "Lệnh thực thi quá lâu và đã bị ngắt (Timeout)."}
    except subprocess.CalledProcessError as e:
        return {"error": f"Lệnh trả về lỗi (Exit Code {e.returncode}): {e.output.decode('utf-8', errors='ignore')}"}
    except Exception as e:
        return {"error": f"Lỗi không xác định khi chạy lệnh: {str(e)}"}

def open_url_in_browser(url: str) -> dict:
    """
    Mở đường dẫn URL hoặc tìm kiếm từ khóa trên trình duyệt web mặc định.
    Hỗ trợ cả Windows và Android Termux.
    Ví dụ: 'google.com', 'https://vnexpress.net', 'tìm quán cafe gần đây'
    """
    # Xử lý input: Nếu là từ khóa tìm kiếm (không phải domain rõ ràng)
    # Logic đơn giản: Nếu có khoảng trắng hoặc không có dấu chấm (.), coi là search query
    if " " in url or "." not in url:
        print(f"[*] System: Phát hiện từ khóa tìm kiếm: '{url}' -> Chuyển hướng sang Google Search.")
        url = f"https://www.google.com/search?q={quote(url)}"
    elif not url.startswith("http"):
        url = "http://" + url

    print(f"[*] System: Đang mở trình duyệt: {url}...")
    
    try:
        # Hỗ trợ riêng cho Termux
        if is_termux():
            # Ưu tiên dùng termux-open (mở app mặc định xử lý link)
            try:
                subprocess.run(["termux-open", url], check=True)
                return {"status": "success", "message": f"Đã mở {url} trên Android (termux-open)."}
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Fallback sang termux-open-url (cần Termux:API)
                try:
                    subprocess.run(["termux-open-url", url], check=True)
                    return {"status": "success", "message": f"Đã mở {url} trên Android (termux-open-url)."}
                except Exception as e:
                    return {"error": f"Lỗi Termux: Không thể mở trình duyệt. Hãy cài 'termux-tools' hoặc 'termux-api'. Chi tiết: {e}"}

        # Windows / PC Standard
        webbrowser.open(url)
        return {"status": "success", "message": f"Đã mở {url} trong trình duyệt mặc định."}
    except Exception as e:
        return {"error": f"Lỗi khi mở trình duyệt: {str(e)}"}

from tools.desktop_tools import capture_screen, get_active_window_info, control_mouse, type_text, scroll_screen, press_key, setup_adb_termux
from tools.vision_tools import analyze_screen, read_screen_text
from agent.memory import learn_new_rule, get_learned_rules

def start_watch_mode(interval=5, max_loops=10):
    """
    Bật chế độ 'Quan sát & Tự học' (Watch Mode).
    AI sẽ liên tục chụp màn hình mỗi N giây, phân tích thay đổi và ghi nhớ hành vi.
    Giả lập khả năng 'nhìn trực tiếp'.
    
    Args:
        interval: Thời gian nghỉ giữa các lần chụp (giây).
        max_loops: Số lần lặp tối đa (để tránh chạy vô hạn tốn API).
    """
    print(f"\n[*] KÍCH HOẠT CHẾ ĐỘ QUAN SÁT (WATCH MODE) - Interval: {interval}s")
    
    if is_termux():
        print("[Note] Trên Termux, hãy đảm bảo đã kết nối ADB (chạy tool setup_adb_termux trước).")
    
    import time
    from PIL import Image
    import imagehash # Cần cài thêm nếu muốn so sánh ảnh thông minh, ở đây dùng size đơn giản
    
    last_analysis = ""
    
    for i in range(max_loops):
        print(f"\n--- WATCH LOOP {i+1}/{max_loops} ---")
        
        # 1. Chụp màn hình
        result = capture_screen()
        if result.get("status") != "success":
            print(f"[!] Lỗi chụp: {result.get('message')}")
            if "Android" in result.get('message', ''):
                print("    -> Gợi ý: Hãy chạy lệnh 'setup_adb_termux' để kết nối ADB.")
                break
            time.sleep(interval)
            continue
            
        # 2. Phân tích (Chỉ gửi AI nếu cần thiết, ở đây demo gửi luôn)
        # Để tiết kiệm, thực tế nên so sánh hash ảnh trước.
        
        print("[*] Đang phân tích màn hình...")
        # Gọi hàm analyze_screen từ vision_tools nhưng xử lý output gọn hơn
        analysis = analyze_screen("Bạn đang thấy gì trên màn hình? Nếu có hành động người dùng (như mở app, gõ phím), hãy ghi chú lại.")
        
        print(f"AI Observation: {analysis}")
        
        # 3. Tự học (Giả lập logic)
        if "facebook" in analysis.lower():
            learn_new_rule("Người dùng thường mở Facebook. Gợi ý: Kiểm tra tin nhắn.")
            print("[+] Learned: Đã ghi nhớ thói quen mở Facebook.")
        
        time.sleep(interval)

    return "Đã kết thúc phiên Quan sát."

def launch_app(app_name: str) -> dict:
    """
    Mở một ứng dụng trên máy tính hoặc điện thoại.
    Args:
        app_name: Tên ứng dụng (vd: 'notepad', 'calc', 'facebook', 'youtube') hoặc Package Name (com.facebook.katana).
    """
    print(f"[*] System: Đang khởi chạy ứng dụng: {app_name}...")
    
    if is_termux():
        # Android Termux Logic
        # 1. Thử dùng monkey để mở package (cần tên gói chính xác)
        try:
            # Mapping tên thông dụng sang package name
            package_map = {
                "facebook": "com.facebook.katana",
                "youtube": "com.google.android.youtube",
                "chrome": "com.android.chrome",
                "zalo": "com.zing.zalo",
                "tiktok": "com.ss.android.ugc.trill",
                "maps": "com.google.android.apps.maps",
                "gmail": "com.google.android.gm",
                "settings": "com.android.settings"
            }
            pkg = package_map.get(app_name.lower(), app_name)
            
            # Lệnh monkey giúp start app mà không cần root (đôi khi hoạt động)
            cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
            subprocess.run(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"status": "success", "message": f"Đã gửi lệnh mở {pkg} trên Android."}
        except Exception as e:
            return {"error": f"Lỗi mở app trên Android: {str(e)}"}
    else:
        # Windows Logic
        try:
            # Mapping tên thông dụng
            app_map = {
                "notepad": "notepad.exe",
                "calc": "calc.exe",
                "explorer": "explorer.exe",
                "cmd": "start cmd.exe",
                "chrome": "start chrome",
                "edge": "start msedge"
            }
            cmd = app_map.get(app_name.lower(), app_name)
            
            os.system(cmd)
            return {"status": "success", "message": f"Đã mở {app_name} trên Windows."}
        except Exception as e:
            return {"error": f"Lỗi mở app trên Windows: {str(e)}"}

# Danh sách các hàm có thể được gọi bởi AI
tools_list = [
    scan_target, check_http_security_headers, get_my_ip, 
    scan_local_network, scan_for_cameras, analyze_website_health, 
    scan_wifi_networks, run_system_command, open_url_in_browser, launch_app,
    # Desktop Automation
    capture_screen, get_active_window_info, control_mouse, type_text, scroll_screen, press_key,
    # Vision
    analyze_screen, read_screen_text,
    # Memory / Learning
    learn_new_rule, get_learned_rules,
    # New Tools
    setup_adb_termux, start_watch_mode
]
