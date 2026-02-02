import math
import pyautogui
import time
import os
import config
import winsound
import ctypes
from PIL import ImageGrab
import numpy as np
import cv2
from utils import get_window_coordinates, capture_rect, log, cv_imread
from recognizers import NumberRecognizer, NameRecognizer, find_grid_points

scanner_my = NumberRecognizer(os.path.join("img", "numbers", "m"))
scanner_market = NumberRecognizer(os.path.join("img", "numbers", "o"))
scanner_name = NameRecognizer()
_last_safe_pos = None
def init_mouse_safety():
    """初始化鼠标位置记录"""
    global _last_safe_pos
    _last_safe_pos = pyautogui.position()

def check_interference(threshold=10):
    global _last_safe_pos
    if _last_safe_pos is None:
        _last_safe_pos = pyautogui.position()
        return False
        
    current_x, current_y = pyautogui.position()
    last_x, last_y = _last_safe_pos
    dist = math.hypot(current_x - last_x, current_y - last_y)
    
    if dist > threshold:
        log(f"⚠️ 检测到鼠标人为移动 (距离: {int(dist)}px)，任务停止")
        return True
    return False

def safe_moveTo(x, y, duration=0.1):
    global _last_safe_pos
    if check_interference(): return False
    pyautogui.moveTo(x, y, duration=duration)
    _last_safe_pos = (x, y)
    return True

def safe_click():
    global _last_safe_pos
    if check_interference(): return False
    pyautogui.click()
    _last_safe_pos = pyautogui.position()
    return True

def identify_current_region_full_screen(win_x, win_y, win_w, win_h):
    screenshot = ImageGrab.grab(bbox=(win_x, win_y, win_x + win_w, win_y + win_h))
    screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    
    zones_dir = os.path.join("img", "zones")
    if not os.path.exists(zones_dir): return None, {}
    
    best_match_key = None; best_match_val = 0
    
    for fname in os.listdir(zones_dir):
        path = os.path.join(zones_dir, fname)
        template = cv_imread(path, cv2.IMREAD_GRAYSCALE)
        if template is None: continue
        
        res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        
        if max_val > config.MATCH_THRESHOLD and max_val > best_match_val:
            best_match_val = max_val
            best_match_key = os.path.splitext(fname)[0]
            
    if best_match_key:
        return best_match_key, config.REGION_DATA.get(best_match_key, {})
        
    return None, {}

def run_job(stop_check_func):
    log("\n>>> 任务已启动")
    init_mouse_safety()
    coords = get_window_coordinates() 
    if not coords or coords[0] is None:
        log(f"❌ 未找到窗口: {config.GAME_WINDOW_TITLE}")
        return
    client_rect, base_origin = coords
    if base_origin is None:
        log("❌ 窗口坐标获取异常")
        return

    win_x, win_y, win_w, win_h = client_rect
    base_x, base_y = base_origin
    
    zone_key, zone_config = identify_current_region_full_screen(win_x, win_y, win_w, win_h)
    if not zone_key:
        log("❌ 未识别到地区"); return
    
    log(f"✅ 识别地区: [{zone_key}]")
    scanner_name.load_zone_templates(zone_key)
    
    marker_name = zone_config.get("marker", "")
    y_filter = zone_config.get("y_filter", 0)
    max_count = zone_config.get("count", 30)
    marker_path = os.path.join("img", "ui", marker_name)
    
    log(f"正在扫描网格... (Anchor: {marker_name})")
    cx, cy, cw, ch = client_rect
    
    padding = 50 
    search_bbox = (cx, cy, cx + cw + padding, cy + ch + padding)
    
    game_screen = ImageGrab.grab(bbox=search_bbox)
    grid_points = find_grid_points(game_screen, marker_path, y_limit=y_filter)
    
    total = len(grid_points)
    log(f"🔍 找到 {total} 个商品 (配置上限: {max_count})")
    if total == 0: return

    results = []
    
    for i, (rel_x, rel_y) in enumerate(grid_points):
        if stop_check_func(): break
        if i >= max_count:
            log(f"已达到配置数量上限 ({max_count})，停止扫描后续物资")
            break
        
        target_x = win_x + rel_x
        target_y = win_y + rel_y

        if not safe_moveTo(target_x, target_y, duration=0.1):
            ctypes.windll.user32.MessageBoxW(0, "检测到鼠标移动，任务已强制停止。", "安全中断", 0x30 | 0x1000)
            return
        
        if not safe_click():
            ctypes.windll.user32.MessageBoxW(0, "检测到鼠标移动，任务已强制停止。", "安全中断", 0x30 | 0x1000)
            return
        
        time.sleep(0.5)
        
        item_name = scanner_name.identify(capture_rect(base_x, base_y, config.AREA_ITEM_NAME))
        my_price = scanner_my.identify(capture_rect(base_x, base_y, config.AREA_MY_PRICE))
        
        if not safe_moveTo(base_x + config.BTN_SWITCH_MARKET_X, base_y + config.BTN_SWITCH_MARKET_Y, duration=0.1):
            ctypes.windll.user32.MessageBoxW(0, "检测到鼠标移动，任务已强制停止。", "安全中断", 0x30 | 0x1000)
            return
        
        if not safe_click(): 
            return
        
        time.sleep(0.8)
        
        top_price = scanner_market.identify(capture_rect(base_x, base_y, config.AREA_MARKET_PRICE))
        diff = top_price - my_price
        log(f"[{i+1}] {item_name}: 自{my_price} -> 卖{top_price} | 差{diff}")
        
        if my_price > 0 and top_price > 0:
            results.append({"name": item_name, "diff": diff, "pos": (win_x + rel_x, win_y + rel_y)})
        if not safe_moveTo(base_x + config.BTN_CLOSE_X, base_y + config.BTN_CLOSE_Y, duration=0.1):
             ctypes.windll.user32.MessageBoxW(0, "检测到鼠标移动，任务已强制停止。", "安全中断", 0x30 | 0x1000)
             return
         
        if not safe_click(): return
        time.sleep(0.3)
        if stop_check_func(): return
        if not safe_click(): return
        time.sleep(0.3)
        
    log("\n<<< 任务结束 >>>")
    
    if results:
        best = sorted(results, key=lambda x: x['diff'], reverse=True)[0]
        log(f"最佳: {best['name']} (差价 {best['diff']})")
        if not safe_moveTo(best['pos'][0], best['pos'][1], duration=0.2):
             ctypes.windll.user32.MessageBoxW(0, "检测到鼠标移动，停止操作", "安全中断", 0x30 | 0x1000)
             return
        time.sleep(0.3)
        if not safe_click(): return
        log(f"已自动点击: {best['name']}")
    else:
        log("未发现高利润物资")
    try:
        winsound.MessageBeep(winsound.MB_OK) 
        log("提示音播放完毕")
    except Exception as e:
        log(f"提示音播放失败: {e}")
    popup_title = "任务完成"
    if results:
        popup_text = f"已找到最佳利润物资：\n{best['name']}\n差价: {best['diff']}"
    else:
        popup_text = "本次扫描未发现高利润物资"
    ctypes.windll.user32.MessageBoxW(0, popup_text, popup_title, 0x40 | 0x1000)