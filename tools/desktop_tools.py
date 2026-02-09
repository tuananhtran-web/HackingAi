import pyautogui
import os
import time
import json
import platform
import subprocess
from datetime import datetime

# Setup screenshot directory
SCREENSHOT_DIR = "screenshots"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

def is_termux_check():
    return "com.termux" in os.environ.get("PREFIX", "")

def capture_screen(filename=None):
    """
    Chụp ảnh màn hình và lưu vào thư mục screenshots.
    Returns: Đường dẫn file ảnh.
    """
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        abs_path = os.path.abspath(filepath)
        
        # Hỗ trợ Android Termux
        if is_termux_check():
            try:
                # Cách 1: Thử dùng /system/bin/screencap (Cần Root hoặc một số máy cho phép)
                try:
                    temp_path = "/sdcard/termux_screenshot.png"
                    subprocess.run(["/system/bin/screencap", "-p", temp_path], check=True, timeout=3, stderr=subprocess.DEVNULL)
                    subprocess.run(["cp", temp_path, abs_path], check=True)
                    return {"status": "success", "filepath": abs_path, "message": "Đã chụp màn hình (Android/Root)."}
                except:
                    pass
                
                # Cách 2: Dùng ADB (Local ADB - Không cần Root)
                # Kiểm tra xem ADB có kết nối không
                adb_check = subprocess.run(["adb", "devices"], capture_output=True, text=True)
                if "device" in adb_check.stdout and "List of devices attached" in adb_check.stdout:
                     # Chụp qua ADB
                     subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/adb_screenshot.png"], check=True)
                     subprocess.run(["adb", "pull", "/sdcard/adb_screenshot.png", abs_path], check=True)
                     return {"status": "success", "filepath": abs_path, "message": "Đã chụp màn hình (ADB No-Root)."}
                
                return {"status": "error", "message": "Android: Không thể chụp màn hình. Hãy cài đặt 'Local ADB' (xem hướng dẫn setup_adb)."}

            except Exception as e:
                return {"status": "error", "message": f"Android Error: {str(e)}"}

        # Windows / Desktop
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        return {"status": "success", "filepath": abs_path, "message": "Đã chụp màn hình thành công."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_active_window_info():
    """
    Lấy thông tin cửa sổ đang hoạt động (Active Window).
    """
    try:
        # PyGetWindow được cài cùng PyAutoGUI
        import pygetwindow as gw
        window = gw.getActiveWindow()
        if window:
            return {
                "title": window.title,
                "left": window.left,
                "top": window.top,
                "width": window.width,
                "height": window.height,
                "status": "success"
            }
        return {"status": "error", "message": "Không tìm thấy cửa sổ active."}
    except ImportError:
         return {"status": "error", "message": "Module pygetwindow không khả dụng (chỉ hỗ trợ Windows)."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def setup_adb_termux():
    """
    Hướng dẫn và cài đặt ADB Local cho Termux (Không Root).
    """
    if not is_termux_check():
        return "Tính năng này chỉ dành cho Android Termux."

    print("\n=== SETUP ADB LOCAL (NO ROOT SCREEN CAPTURE) ===")
    print("Để AI có thể 'nhìn' màn hình mà không cần Root, chúng ta dùng ADB qua Wifi.")
    
    # 1. Kiểm tra/Cài đặt android-tools
    if subprocess.run(["which", "adb"], capture_output=True).returncode != 0:
        print("[*] Đang cài đặt 'android-tools'...")
        try:
            subprocess.run(["pkg", "install", "android-tools", "-y"], check=True)
            print("[+] Đã cài đặt android-tools.")
        except:
            return "[-] Lỗi cài đặt android-tools. Hãy chạy 'pkg install android-tools' thủ công."

    # 2. Hướng dẫn kết nối
    print("\n--- HƯỚNG DẪN KẾT NỐI ---")
    print("1. Bật 'Developer Options' (Tùy chọn nhà phát triển) trên điện thoại.")
    print("2. Bật 'Wireless Debugging' (Gỡ lỗi không dây).")
    print("3. Chọn 'Pair device with pairing code'.")
    print("4. Nhập lệnh sau vào Termux (trên terminal mới hoặc split screen):")
    print("   adb pair <IP>:<PORT> <CODE>")
    print("   (Ví dụ: adb pair 192.168.1.5:45678 123456)")
    print("5. Sau khi pair thành công, chạy lệnh connect:")
    print("   adb connect <IP>:<PORT> (Port thường khác với port pair)")
    
    input("\nSau khi đã kết nối ADB thành công, nhấn Enter để kiểm tra...")
    
    # 3. Kiểm tra kết nối
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    if "device" in res.stdout and "List of devices attached" in res.stdout and len(res.stdout.strip().split('\n')) > 1:
        return "[+] ADB Connected! AI đã có thể nhìn màn hình."
    else:
        return f"[-] Chưa thấy thiết bị ADB. Output:\n{res.stdout}\nHãy thử lại."

def control_mouse(action, x=None, y=None, duration=0.5):
    """
    Điều khiển chuột.
    action: 'click', 'double_click', 'move', 'right_click'
    x, y: Tọa độ (nếu None sẽ dùng vị trí hiện tại)
    """
    try:
        # Nếu là Termux, dùng ADB input tap/swipe
        if is_termux_check():
            if action == 'click' and x is not None and y is not None:
                subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])
                return {"status": "success", "message": f"ADB Tap ({x},{y})"}
            elif action == 'move':
                pass # ADB không có move chuột ảo dễ dàng
            elif action == 'swipe' and x is not None and y is not None:
                # Giả sử vuốt từ (x,y) tới (x,y-500)
                subprocess.run(["adb", "shell", "input", "swipe", str(x), str(y), str(x), str(y-300)])
                return {"status": "success", "message": f"ADB Swipe Up"}
            
            return {"status": "success", "message": "Đã gửi lệnh ADB Input."}

        screen_width, screen_height = pyautogui.size()
        
        if x is not None and y is not None:
            # Kiểm tra an toàn
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                 return {"status": "error", "message": f"Tọa độ ({x},{y}) nằm ngoài màn hình ({screen_width}x{screen_height})."}
            pyautogui.moveTo(x, y, duration=duration)
            
        if action == 'click':
            pyautogui.click()
        elif action == 'double_click':
            pyautogui.doubleClick()
        elif action == 'right_click':
            pyautogui.rightClick()
        elif action == 'move':
            pass # Đã move ở trên
        else:
            return {"status": "error", "message": f"Hành động '{action}' không hợp lệ."}
            
        return {"status": "success", "message": f"Đã thực hiện {action} tại ({x}, {y})"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def type_text(text, interval=0.1):
    """
    Nhập văn bản (Type text).
    """
    try:
        pyautogui.write(text, interval=interval)
        return {"status": "success", "message": f"Đã nhập: {text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def press_key(key):
    """
    Nhấn một phím (vd: 'enter', 'esc', 'f1').
    """
    try:
        pyautogui.press(key)
        return {"status": "success", "message": f"Đã nhấn phím: {key}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def scroll_screen(amount):
    """
    Cuộn màn hình (amount > 0: lên, amount < 0: xuống).
    """
    try:
        pyautogui.scroll(amount)
        return {"status": "success", "message": f"Đã cuộn {amount} đơn vị."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
