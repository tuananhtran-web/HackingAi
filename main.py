import sys
import os
from agent.core import SecurityAgent
# Import tool utils để check môi trường
from tools.network_tools import check_and_install_termux_dependencies

def main():
    # Kiểm tra dependency Termux ngay khi khởi động
    check_and_install_termux_dependencies()

    print("=================================================================")
    print("   AI SECURITY ASSISTANT - MÔI TRƯỜNG THỬ NGHIỆM & ĐÀO TẠO")
    print("=================================================================")
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
