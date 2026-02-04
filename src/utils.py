# utils.py
import os
import time
import math
import logging
import uuid
import pyautogui
import win32gui, win32con
from PIL import ImageGrab
from datetime import datetime
import config
import ctypes

ui_callback = None

def init_logger():
    if config.LOG:
        if not os.path.exists(config.LOG_DIR):
            os.makedirs(config.LOG_DIR, exist_ok=True)
        file_name = f"log_{datetime.now().strftime('%Y-%m-%d')}.txt"
        full_path = os.path.join(config.LOG_DIR, file_name)

        logging.basicConfig(filename=full_path,
                            level=logging.INFO, encoding='utf-8',
                            format='%(asctime)s - %(message)s')

def set_ui_callback(callback):
    global ui_callback
    ui_callback = callback

def log(msg):
    print(msg)
    if config.LOG: logging.info(msg)
    if ui_callback: ui_callback(msg)

_last_safe_pos = None

def init_mouse_safety():
    global _last_safe_pos
    _last_safe_pos = pyautogui.position()

def safe_action(func, *args, **kwargs):
    global _last_safe_pos
    if _last_safe_pos is None: _last_safe_pos = pyautogui.position()
    
    cur_x, cur_y = pyautogui.position()
    last_x, last_y = _last_safe_pos
    dist = math.hypot(cur_x - last_x, cur_y - last_y)
    if dist > 50:
        msg = f"⚠️ 检测到鼠标人为移动，任务停止\n距离上次鼠标位置：{dist}px"
        log(msg)
        ctypes.windll.user32.MessageBoxW(0, msg, "安全中断", 0x40 | 0x1000)
        return False

    func(*args, **kwargs)
    _last_safe_pos = pyautogui.position()
    return True

def safe_click(): return safe_action(pyautogui.click)
def safe_move(x, y): return safe_action(pyautogui.moveTo, x, y, duration=0)

def snapshot(region=None):
    try:
        bbox = (region[0], region[1], region[0]+region[2], region[1]+region[3]) if region else None
        img = ImageGrab.grab(bbox=bbox)
        offset = (region[0], region[1]) if region else (0, 0)
        return img, offset
    except Exception as e:
        log(f"截图失败: {e}")
        return None, (0, 0)

def get_game_window():
    hwnd = win32gui.FindWindow(None, config.GAME_WINDOW_TITLE)
    if not hwnd: return None
    if win32gui.IsIconic(hwnd): win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    pt = win32gui.ClientToScreen(hwnd, (0, 0))
    _, _, w, h = win32gui.GetClientRect(hwnd)
    return (pt[0], pt[1], w, h)

def get_temp_path(prefix="img", extension="png"):
    date_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(config.TMP_DIR, date_str)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4()}.{extension}"
    return os.path.abspath(os.path.join(folder_path, filename))