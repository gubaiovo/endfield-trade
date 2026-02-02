# recognizers.py
import cv2
import numpy as np
import os
import config
import time
from utils import cv_imread, cv_imwrite, log

class NumberRecognizer:
    def __init__(self, folder):
        self.templates = {}
        self.load_templates(folder)

    def load_templates(self, folder):
        if not os.path.exists(folder): return
        for i in range(10):
            for ext in ['.png', '.jpg']:
                path = os.path.join(folder, f"{i}{ext}")
                if os.path.exists(path):
                    img = cv_imread(path, cv2.IMREAD_GRAYSCALE)
                    if img is not None: self.templates[i] = img; break

    def identify(self, screen_img, threshold=0.85):
        if screen_img is None: return 0
        screen_np = np.array(screen_img)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
        
        s_h, s_w = screen_gray.shape[:2]
        
        matches = []
        for digit, template in self.templates.items():
            t_h, t_w = template.shape[:2]
            if s_h < t_h or s_w < t_w: continue
                
            res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= threshold)
            for pt in zip(*loc[::-1]): matches.append((pt[0], digit))
            
        if not matches: return 0
        matches.sort(key=lambda x: x[0])
        clean_matches = []
        last_x = -100
        for x, digit in matches:
            if x - last_x > 4: clean_matches.append(digit); last_x = x
        try: return int("".join(map(str, clean_matches)))
        except: return 0

class NameRecognizer:
    def __init__(self, base_folder="img/names"):
        self.base_folder = base_folder
        self.current_zone_templates = {}
        self.current_zone_name = "unknown"

    def load_zone_templates(self, zone_name_no_ext):
        self.current_zone_name = zone_name_no_ext
        target_path = os.path.join(self.base_folder, zone_name_no_ext)
        self.current_zone_templates = {}
        if not os.path.exists(target_path): os.makedirs(target_path); return
        log(f"加载物品名库: {zone_name_no_ext}")
        for fname in os.listdir(target_path):
            if fname.lower().endswith(('.png', '.jpg')):
                path = os.path.join(target_path, fname)
                img = cv_imread(path, cv2.IMREAD_GRAYSCALE)
                if img is not None: self.current_zone_templates[os.path.splitext(fname)[0]] = img

    def identify(self, screen_img):
        if screen_img is None: return "未知商品"
        screen_np = np.array(screen_img)
        screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
        
        s_h, s_w = screen_gray.shape[:2]
        
        best_match = None; best_val = 0
        for name, template in self.current_zone_templates.items():
            t_h, t_w = template.shape[:2]
            if s_h < t_h or s_w < t_w: continue
                
            try:
                res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val > best_val: best_val = max_val; best_match = name
            except: pass
            
        if best_match and best_val >= config.MATCH_THRESHOLD: return best_match
        else:
            ts = int(time.time())
            save_path = os.path.join(self.base_folder, self.current_zone_name, f"unknown_{ts}.png")
            if not os.path.exists(os.path.dirname(save_path)): os.makedirs(os.path.dirname(save_path))
            cv_imwrite(save_path, cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR))
            return "未知商品"

def find_grid_points(screen_img, template_path, threshold=0.8, min_dist=10, y_limit=0):
    if not os.path.exists(template_path):
        log(f"⚠️ Marker图片缺失: {template_path}")
        return []

    template = cv_imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None: return []

    screen_np = np.array(screen_img)
    screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)

    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    
    h, w = template.shape
    points = []
    
    for pt in zip(*loc[::-1]): 
        if pt[1] < y_limit: continue
        center_x, center_y = pt[0] + w//2, pt[1] + h//2
        points.append((center_x, center_y))

    unique_points = []
    for pt in points:
        is_close = False
        for existing_pt in unique_points:
            dist = ((pt[0]-existing_pt[0])**2 + (pt[1]-existing_pt[1])**2)**0.5
            if dist < min_dist:
                is_close = True; break
        if not is_close: unique_points.append(pt)

    unique_points.sort(key=lambda k: (k[1] // 20, k[0]))
    return unique_points