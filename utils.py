# utils.py
import cv2
import numpy as np
import os
import win32gui # type: ignore
import win32con # type: ignore
from PIL import ImageGrab
import logging
from datetime import datetime
import config

ui_callback = None

def init_logger():
    if config.LOG:
        log_filename = f"log_{datetime.now().strftime('%Y-%m-%d')}.txt"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            filename=log_filename,
            filemode='a',
            encoding='utf-8'
        )

def set_ui_callback(callback):
    global ui_callback
    ui_callback = callback

def log(msg):
    print(msg)
    if config.LOG: logging.info(msg)
    if ui_callback: ui_callback(msg)

def cv_imread(file_path, flags=cv2.IMREAD_COLOR):
    try:
        raw_data = np.fromfile(file_path, dtype=np.uint8)
        img = cv2.imdecode(raw_data, flags)
        return img
    except: return None

def cv_imwrite(file_path, img):
    try:
        ext = os.path.splitext(file_path)[1]
        result, img_data = cv2.imencode(ext, img)
        if result:
            img_data.tofile(file_path)
            return True
        return False
    except: return False

def get_window_coordinates():
    try:
        hwnd = win32gui.FindWindow(None, config.GAME_WINDOW_TITLE)
        if not hwnd: return None, None

        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        client_point = win32gui.ClientToScreen(hwnd, (0, 0))
        client_x, client_y = client_point
        _, _, width, height = win32gui.GetClientRect(hwnd)
        
        base_x = client_x - config.BORDER_WIDTH
        base_y = client_y - config.TITLE_BAR_HEIGHT
        
        return (client_x, client_y, width, height), (base_x, base_y)

    except Exception as e:
        log(f"获取窗口失败: {e}")
        return None, None

def capture_rect(base_x, base_y, rect_config):
    rx, ry, rw, rh = rect_config
    return ImageGrab.grab(bbox=(base_x + rx, base_y + ry, base_x + rx + rw, base_y + ry + rh))