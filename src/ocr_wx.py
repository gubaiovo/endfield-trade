import os
from typing import List, Dict, Any, cast
from wx_ocr import ocr
from utils import snapshot, log, get_temp_path 
import config

def find_grid_items_with_names(region, suffix="货组"):
    pil_img, offset = snapshot(region)
    if not pil_img: return []
    full_path = get_temp_path(prefix="wx_scan")
    pil_img.save(full_path)
    items_found = []
    try:
        raw_result = ocr(full_path)
        results = cast(List[Dict[str, Any]], raw_result)
        if not results: results = []
        for item in results:
            if not isinstance(item, dict): continue
            text = str(item.get('text', ''))
            if suffix in text and "详情" not in text:
                box = item.get('location')
                if isinstance(box, dict):
                    try:
                        left = int(box.get('left', 0))
                        right = int(box.get('right', 0))
                        top = int(box.get('top', 0))
                        bottom = int(box.get('bottom', 0))
                        cx = int((left + right) / 2) + offset[0]
                        cy = int((top + bottom) / 2) + offset[1]      
                        items_found.append({
                            'name': text,
                            'pos': (cx, cy)
                        })
                    except: continue
    except Exception as e:
        log(f"WxOCR 扫描失败: {e}")
    finally:
        if os.path.exists(full_path) and not getattr(config, 'DEBUG_MODE', False):
            try:
                os.remove(full_path)
            except: pass

    items_found.sort(key=lambda k: (k['pos'][1] // 50, k['pos'][0]))
    return items_found