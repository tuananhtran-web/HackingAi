import google.generativeai as genai
import os
import time
from PIL import Image
from tools.desktop_tools import capture_screen
import config

# Cấu hình API cho vision tool (sử dụng chung config)
if config.GOOGLE_API_KEY:
    genai.configure(api_key=config.GOOGLE_API_KEY)

def analyze_screen(prompt="Mô tả chi tiết những gì bạn thấy trên màn hình."):
    """
    Chụp màn hình và phân tích nội dung hình ảnh bằng AI Vision.
    Hữu ích khi người dùng hỏi: "Trên màn hình có gì?", "Đọc lỗi này giúp tôi", "Nút bấm nằm ở đâu?".
    """
    try:
        # 1. Chụp màn hình
        print(f"\n[*] Vision Tool: Đang chụp màn hình...")
        result = capture_screen()
        if result.get("status") != "success":
            return f"Lỗi chụp màn hình: {result.get('message')}"
        
        filepath = result["filepath"]
        print(f"[*] Vision Tool: Đã chụp {filepath}. Đang gửi lên AI...")
        
        # 2. Upload và phân tích (Dùng model Vision)
        # Lưu ý: Chúng ta dùng model Flash vì nó nhanh và hỗ trợ Multimodal
        # Cập nhật model name chính xác từ danh sách hỗ trợ (gemini-2.5-flash)
        model_name = getattr(config, 'MODEL_NAME', 'gemini-2.5-flash')
        model = genai.GenerativeModel(model_name)
        
        img = Image.open(filepath)
        
        # Gửi request: Prompt + Image
        response = model.generate_content([prompt, img])
        
        print(f"[*] Vision Tool: Đã phân tích xong.")
        return f"Kết quả phân tích màn hình:\n{response.text}"
        
    except Exception as e:
        return f"Lỗi Vision Tool: {str(e)}"

def read_screen_text():
    """
    Đọc toàn bộ văn bản xuất hiện trên màn hình (OCR).
    """
    return analyze_screen("Hãy trích xuất toàn bộ văn bản (text) bạn thấy trong hình ảnh này. Chỉ trả về nội dung văn bản.")
