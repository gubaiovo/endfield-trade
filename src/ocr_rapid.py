import numpy as np
import re
from rapidocr import RapidOCR, EngineType
from utils import snapshot, log, safe_move, safe_click
import config

try:
    engine = RapidOCR(
        params={
            "Det.engine_type": EngineType.OPENVINO,
            "Cls.engine_type": EngineType.OPENVINO,
            "Rec.engine_type": EngineType.OPENVINO,
        }
    )
except Exception as e:
    print(f"OpenVINO 引擎初始化失败: {e}")
    engine = RapidOCR()

def check_text_exists(keyword, region=None):
    ocr_result, _ = scan_raw_object(region)
    texts = extract_texts_from_result(ocr_result)
    for text in texts:
        if keyword in text:
            return True
    return False

def scan_raw_object(region=None):
    pil_img, offset = snapshot(region)
    if not pil_img: return None, (0,0)
    
    img_np = np.array(pil_img)
    try:
        ocr_result = engine(img_np, use_det=True, use_cls=False, use_rec=True)
        return ocr_result, offset
    except Exception as e:
        log(f"RapidOCR 异常: {e}")
        return None, (0,0)

def extract_texts_from_result(ocr_result):
    if ocr_result is None: 
        return []
    txts = getattr(ocr_result, 'txts', None)
    if txts is not None:
        texts = list(txts)
        if config.DEBUG_MODE:
            log(f"OCR Texts: {texts}")
        return texts
        
    return []

def get_name_from_list(text_list, suffix="货组"):
    for text in text_list:
        if suffix in text: 
            return text
    return "未知商品"

def get_price_from_list(text_list, keywords):
    for i, text in enumerate(text_list):
        if any(kw in text for kw in keywords):
            if i + 1 < len(text_list):
                next_text = text_list[i+1]
                nums = re.findall(r'\d+', next_text)
                if nums:
                    return int(nums[0])
    return 0

def get_market_max_from_list(text_list):
    prices = []
    for text in text_list:
        if any(c in text for c in ['%', 'UID', '/', ':', '+', '-']): continue
        
        if text.isdigit():
            val = int(text)
            if 100 <= val <= 99999:
                prices.append(val)
    
    return max(prices) if prices else 0

def click_text(keyword, region=None, cached_result=None, offset=(0,0)):
    if cached_result is None:
        ocr_result, offset = scan_raw_object(region)
    else:
        ocr_result = cached_result

    if ocr_result is None:
        return False

    boxes = getattr(ocr_result, 'boxes', None)
    txts = getattr(ocr_result, 'txts', None)

    if boxes is None or txts is None:
        return False

    for box, text in zip(boxes, txts):
        if keyword in text:
            try:
                p1, p3 = box[0], box[2]
                cx = int((p1[0] + p3[0]) / 2) + offset[0]
                cy = int((p1[1] + p3[1]) / 2) + offset[1]
                log(f">>> 点击: [{text}]")
                safe_move(cx, cy)
                safe_click()
                return True
            except Exception as e:
                log(f"坐标计算错误: {e}")      
    return False