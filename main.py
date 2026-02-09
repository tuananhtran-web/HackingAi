import sys
import os
import time
from agent.core import SecurityAgent
# Import tool utils để check môi trường
from tools.network_tools import (
    check_and_install_termux_dependencies, 
    scan_local_network, 
    scan_for_cameras, 
    scan_wifi_networks,
    get_my_ip,
    request_termux_permissions # Import thêm hàm xin quyền
)
# Import module giả lập
from tools.attack_simulation import simulate_deauth_attack, simulate_fake_ap, simulate_wifi_crack
from tools.network_tools import launch_app, start_watch_mode, setup_adb_termux

def run_offline_mode():
    """
    Chế độ chạy Offline không cần AI, cung cấp các công cụ quét an toàn.
    """
    print("\n=================================================================")
    print("   AI SECURITY ASSISTANT - OFFLINE MODE (TOOLKIT)")
    print("=================================================================")
    print("[*] Đang chạy ở chế độ Offline. Các tính năng AI sẽ bị tắt.")
    print("[*] Hỗ trợ DEMO/TESTING nội bộ.")
    print("=================================================================\n")
    
    # Tự động check quyền khi vào chế độ Offline trên Termux
    request_termux_permissions()

    while True:
        print("\n--- DANH SÁCH CÔNG CỤ (OFFLINE) ---")
        print("1. Quét thiết bị trong mạng LAN (Find Devices)")
        print("2. Tìm kiếm Camera IP (Find Cameras)")
        print("3. Quét mạng WiFi (Audit & Security Check)")
        print("4. Xem thông tin IP của tôi (My IP Info)")
        print("5. Kiểm tra gói hỗ trợ Termux (Check Dependencies)")
        print("6. Mở ứng dụng (Launch App)")
        print("7. [BETA] Setup ADB (No-Root Screen Capture)")
        print("8. [BETA] Chế độ Quan sát (Watch Mode)")
        
        print("\n--- DEMO / SIMULATION (CHẾ ĐỘ GIẢ LẬP) ---")
        print("9. Giả lập tấn công Deauth (Simulate Deauth)")
        print("10. Giả lập Fake AP (Simulate Fake AP)")
        print("11. Giả lập Crack WiFi (Simulate WPA Crack)")
        print("0. Thoát (Exit)")
        
        choice = input("\n[Offline] Chọn chức năng (0-11): ").strip()
        
        if choice == '1':
            print("\n[*] Đang quét mạng LAN...")
            result = scan_local_network()
            print(result)
        elif choice == '2':
            print("\n[*] Đang tìm kiếm Camera...")
            result = scan_for_cameras()
            print(result)
        elif choice == '3':
            print("\n[*] Đang quét WiFi...")
            result = scan_wifi_networks()
            if "display" in result:
                print(result["display"])
            else:
                print(result)
        elif choice == '4':
            print("\n[*] Thông tin IP:")
            print(get_my_ip())
        elif choice == '5':
            check_and_install_termux_dependencies()
        elif choice == '6':
            app_name = input("Nhập tên App hoặc Package Name (vd: facebook, youtube): ")
            print(launch_app(app_name))
        elif choice == '7':
            print(setup_adb_termux())
        elif choice == '8':
            start_watch_mode()
        elif choice == '9':
            simulate_deauth_attack()
        elif choice == '10':
            simulate_fake_ap()
        elif choice == '11':
            simulate_wifi_crack()
        elif choice == '0':
            print("Tạm biệt!")
            sys.exit()
        else:
            print("[!] Lựa chọn không hợp lệ.")
        
        input("\nNhấn Enter để tiếp tục...")

def main():
    # Kiểm tra dependency Termux ngay khi khởi động
    check_and_install_termux_dependencies()

    print("=================================================================")
    print("   AI SECURITY ASSISTANT - MÔI TRƯỜNG THỬ NGHIỆM & ĐÀO TẠO")
    print("=================================================================")
    print("Chọn chế độ hoạt động:")
    print("1. AI Online Mode (Mặc định - Cần Internet & API Key)")
    print("2. Offline Toolkit (Không cần Internet - Chỉ công cụ cơ bản)")
    
    mode = input("Nhập lựa chọn (1/2): ").strip()
    
    if mode == '2':
        run_offline_mode()
        return

    # Load AI Agent
    try:
        agent = SecurityAgent()
    except Exception as e:
        print(f"\n[!] Lỗi khởi tạo AI Agent: {e}")
        print("    -> Chuyển sang chế độ Offline Toolkit...")
        time.sleep(2)
        run_offline_mode()
        return

    print("Chào mừng! Tôi là trợ lý AI hỗ trợ bạn tìm hiểu và kiểm thử an ninh mạng.")
    print("Tôi có thể giúp bạn:")
    print(" - Quét cổng để kiểm tra dịch vụ (scan <ip/domain>)")
    print(" - Kiểm tra các header bảo mật của website (check <url>)")
    print(" - Giải thích các khái niệm bảo mật và cách phòng chống tấn công.")
    print("\nLưu ý: Chỉ sử dụng trên hệ thống bạn sở hữu hoặc được phép.")
    print("Gõ 'exit', 'quit' hoặc 'bye' để thoát chương trình.\n")

    agent = SecurityAgent()
    
    if not agent.model:
        print("Không thể khởi động Agent. Kiểm tra lại cấu hình.")
        return

    while True:
        try:
            user_input = input("\n[User]> ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Tạm biệt! Hẹn gặp lại.")
                break
            
            if not user_input:
                continue

            print("\n[AI] Đang phân tích và thực hiện...", end="\r")
            
            # Gọi AI Agent
            response = agent.send_message(user_input)
            
            # Xóa dòng "Đang phân tích..."
            print(" " * 50, end="\r")
            
            print(f"[AI]> {response}")
            
        except KeyboardInterrupt:
            print("\nĐã hủy bởi người dùng.")
            break
        except Exception as e:
            print(f"\nLỗi không mong muốn: {e}")

if __name__ == "__main__":
    main()
