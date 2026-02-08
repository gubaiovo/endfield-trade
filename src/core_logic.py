import time
import ctypes
import pyautogui
import config
from utils import log, get_game_window, safe_move, safe_click, init_mouse_safety
import ocr_wx     
import ocr_rapid  

def run_job(stop_signal):
    log(">>> 任务启动")
    init_mouse_safety()
    
    rect = get_game_window()
    if not rect:
        log("❌ 未找到游戏窗口"); return
    win_x, win_y, win_w, win_h = rect

    grid_area = (win_x, win_y + 150, win_w, win_h - 200)
    max_count = getattr(config, 'MAX_SCAN_COUNT', 12)
    
    log("正在获取物资列表...")
    items_data = ocr_wx.find_grid_items_with_names(grid_area, suffix="货组")
    if not items_data:
        log("❌ 未找到物资"); return
    
    log(f"✅ 发现 {len(items_data)} 个物资")
    for item in items_data:
        log(f"[{item['pos'][1] // 50}, {item['pos'][0] // 50}] {item['name']}")
    results = []

    for i, item in enumerate(items_data):
        if stop_signal(): return
        if i >= max_count: break

        name = item['name']
        gx, gy = item['pos']

        if not safe_move(gx, gy): return
        log(f"\n正在扫描{name}, 位于 [{gx}, {gy}]")
        safe_click()
        time.sleep(0.8)

        detail_area = (win_x + win_w//3, win_y, win_w*2//3, win_h)

        raw_obj, offset = ocr_rapid.scan_raw_object(detail_area)
        
        # raw_obj.vis(f"raw_obj_{i}.png")
        
        text_list = ocr_rapid.extract_texts_from_result(raw_obj)
        
        my_price = ocr_rapid.get_price_from_list(text_list, ["今日售价", "单价", "成本", "售价", "调度卷"])
        
        found_btn = ocr_rapid.click_text("查看好友价格", cached_result=raw_obj, offset=offset)
        
        if not found_btn:
            log(f"[{i+1}] {name}: 无法查看好友价格，跳过")
            pyautogui.press('esc')
            time.sleep(0.5)
            continue
            
        top_price = 0
        wait_start = time.time()
        
        while time.time() - wait_start < 8:
            raw_market, _ = ocr_rapid.scan_raw_object(detail_area)
            # raw_market.vis(f"raw_market_{i}.png")
            market_texts = ocr_rapid.extract_texts_from_result(raw_market)
            
            is_loading = False
            for txt in market_texts:
                if "加载中" in txt:
                    is_loading = True
                    break
            
            if is_loading:
                log("⏳ 数据加载中...")
                time.sleep(0.5)
                continue
            
            top_price = ocr_rapid.get_market_max_from_list(market_texts)
            
            if top_price > 0:
                break
            
            time.sleep(0.3)
            
        if top_price == 0:
            log(f"⚠️ {name}: 获取市场价格超时或失败")
        
        diff = top_price - my_price
        log(f"[{i+1}] {name}: {my_price} -> {top_price} | 利润: {diff}")
        
        if my_price > 0 and top_price > 0:
            results.append({"name": name, "diff": diff, "pos": (gx, gy), "my_price": my_price, "top_price": top_price})

        pyautogui.press('esc')
        time.sleep(0.5) 
        pyautogui.press('esc')
        time.sleep(0.5) 

        if stop_signal(): return

    log("\n<<< 扫描结束 >>>")
    if results:
        for idx, result in enumerate(results):
            log(f"[{idx+1}] {result['name']}: 本价{result['my_price']} -> 好友最高{result['top_price']} | 利润: {result['diff']}")
            
        best = sorted(results, key=lambda x: x['diff'], reverse=True)[0]
        safe_move(*best['pos'])
        time.sleep(0.2)
        safe_click()
        msg = f"最佳物品: {best['name']}\n利润: {best['diff']}"
        ctypes.windll.user32.MessageBoxW(0, msg, "完成", 0x40 | 0x1000)
    else:
        log("未发现有利润物资")