import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
# File .env phải nằm trong cùng thư mục với main.py hoặc thư mục gốc của project
load_dotenv()

# Lấy API Key từ biến môi trường
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    print("CẢNH BÁO: Chưa tìm thấy GEMINI_API_KEY trong biến môi trường hoặc file .env")

# Cấu hình model
# Sử dụng gemini-2.5-flash (Model mới nhất trong danh sách hỗ trợ)
MODEL_NAME = "gemini-2.5-flash" 
