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
        market_header_y = -1 
        has_owned_header = False 
        
        for item in results:
            if not isinstance(item, dict): continue
            text = str(item.get('text', ''))
            
            if "市场" in text:
                box = item.get('location', {})
                if isinstance(box, dict):
                    market_header_y = int(box.get('bottom', 0))
            
            if "当前拥有" in text:
                has_owned_header = True

        should_skip_all = False
        
        if market_header_y > 0:
            if getattr(config, 'DEBUG_MODE', False):
                log(f"识别到: '市场' (Y={market_header_y})，过滤上方内容")
            
        elif has_owned_header:
            log("识别到 '当前拥有' 且无 '市场'，判定为全持有页，跳过")
            should_skip_all = True
            
        else:
            pass

        if should_skip_all:
            if os.path.exists(full_path) and not getattr(config, 'DEBUG_MODE', False):
                os.remove(full_path)
            return []
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
                        
                        if market_header_y > 0:
                            item_cy = (top + bottom) // 2
                            if item_cy < market_header_y:
                                continue
                        cx = int((left + right) / 2) + offset[0]
                        cy = int((top + bottom) / 2) + offset[1]
                        
                        items_found.append({
                            'name': text,
                            'pos': (cx, cy)
                        })
                    except (ValueError, TypeError):
                        continue
                
    except Exception as e:
        log(f"WxOCR 扫描失败: {e}")
    finally:
        if os.path.exists(full_path) and not getattr(config, 'DEBUG_MODE', False):
            try:
                os.remove(full_path)
            except: pass
    items_found.sort(key=lambda k: (k['pos'][1] // 50, k['pos'][0]))
    return items_found