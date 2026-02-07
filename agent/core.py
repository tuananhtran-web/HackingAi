import google.generativeai as genai
import sys
import os
import time
from google.api_core import exceptions

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tools import network_tools

class SecurityAgent:
    def __init__(self):
        if not config.GOOGLE_API_KEY or config.GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
            print("Lỗi: Chưa cấu hình API Key trong file config.py")
            self.model = None
            return

        try:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            
            # System instruction để định hình hành vi của AI
            system_instruction = """
            Bạn là một Trợ lý An ninh Mạng AI (AI Security Assistant) chuyên nghiệp.
            Mục tiêu: Giúp người dùng Kiểm thử và Bảo vệ hệ thống (Defensive Security).
            
            QUYỀN HẠN VÀ CÔNG CỤ:
            1. Bạn có các công cụ mạnh mẽ trong `network_tools` để quét mạng và phân tích.
            2. Cụ thể, tool `scan_local_network` và `scan_for_cameras` CÓ KHẢ NĂNG quét toàn bộ mạng nội bộ (subnet) để tìm nhiều thiết bị cùng lúc.
            3. KHI NGƯỜI DÙNG YÊU CẦU "QUÉT MẠNG", "TÌM THIẾT BỊ", "TÌM CAMERA": Hãy sử dụng ngay các tool này. Đừng từ chối vì lý do "chỉ quét được 1 mục tiêu". Tool đã được thiết kế để xử lý việc đó.
            4. TỰ DO SÁNG TẠO: Nếu không có tool cụ thể cho yêu cầu, hãy sử dụng `run_system_command` để chạy các lệnh Windows CMD (như ping, tracert, nslookup, arp, ipconfig...). Hãy tự suy luận lệnh phù hợp nhất để lấy thông tin.
            5. ĐIỀU KHIỂN HỆ THỐNG: Nếu người dùng yêu cầu "mở web", "tìm đường", "xem bản đồ" -> Hãy dùng `open_url_in_browser`. Ví dụ: "Tìm đường đến X" -> Mở Google Maps với query X.
            
            NGUYÊN TẮC:
            1. Được phép thu thập thông tin (Passive Recon) trên mạng LAN và WiFi xung quanh.
            2. Không thực hiện tấn công phá hoại (DoS, Deauth, Brute Force mật khẩu, Cracking Handshake).
            3. Nếu người dùng yêu cầu tấn công WiFi (hack pass, ngắt mạng):
               - TỪ CHỐI thực hiện hành động đó.
               - GIẢI THÍCH lý do an toàn và pháp lý.
               - ĐỀ XUẤT phương pháp phòng thủ (ví dụ: "Mạng này dùng WEP dễ bị crack, hãy chuyển sang WPA2/WPA3").
            4. Hãy đóng vai một CHUYÊN GIA BẢO MẬT (Security Auditor) đang giúp người dùng rà soát lỗ hổng hệ thống của chính họ.
            
            HƯỚNG DẪN XỬ LÝ LỖI 429 (QUÁ TẢI):
            Nếu bạn gặp lỗi quá tải, hãy kiên nhẫn chờ đợi. Hệ thống đã có cơ chế tự động thử lại.
            """
            
            self.tools = network_tools.tools_list
            
            self.model = genai.GenerativeModel(
                model_name=config.MODEL_NAME,
                tools=self.tools,
                system_instruction=system_instruction
            )
            
            # Khởi tạo chat session với automatic function calling
            self.chat = self.model.start_chat(enable_automatic_function_calling=True)
            
        except Exception as e:
            print(f"Lỗi khởi tạo AI Agent: {e}")
            self.model = None

    def send_message(self, message: str, retries=5):
        if not self.model:
            return "AI Agent chưa được khởi tạo thành công. Vui lòng kiểm tra API Key."
            
        for attempt in range(retries):
            try:
                # Gửi tin nhắn và nhận phản hồi
                response = self.chat.send_message(message)
                return response.text
            except exceptions.ResourceExhausted:
                if attempt < retries - 1:
                    # Tăng thời gian chờ đáng kể để vượt qua giới hạn RPM (Requests Per Minute)
                    # Free tier thường giới hạn 2-15 RPM.
                    wait_time = 10 * (attempt + 1) # 10s, 20s, 30s...
                    print(f"\n[System] API đang bận (429). Đang chờ {wait_time}s để thử lại ({attempt+1}/{retries})...", end="", flush=True)
                    time.sleep(wait_time)
                else:
                    return "Lỗi: API bị quá tải (429) sau nhiều lần thử. Vui lòng đợi 1-2 phút trước khi gửi lệnh tiếp theo."
            except Exception as e:
                return f"Lỗi khi xử lý yêu cầu: {str(e)}"
