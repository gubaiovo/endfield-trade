import keyboard
import threading
import os
from utils import init_logger, log
from core_logic import run_job

is_running = False
work_thread = None

def get_running_status():
    global is_running
    return not is_running

def job_wrapper():
    global is_running
    run_job(get_running_status)
    is_running = False

def start_thread():
    global is_running, work_thread
    if is_running:
        log("任务已经在运行中")
        return
    
    is_running = True
    work_thread = threading.Thread(target=job_wrapper)
    work_thread.daemon = True
    work_thread.start()

def stop_thread():
    global is_running
    if is_running:
        log("\n🛑 正在停止...")
        is_running = False
    else:
        log("当前没有任务在运行。")

if __name__ == "__main__":
    init_logger()
    
    for d in ["img/numbers/m", "img/numbers/o", "img/zones", "img/names", "img/ui"]:
        if not os.path.exists(d): 
            log(f"创建目录: {d}")
            os.makedirs(d)
            
    log("=== 终末地倒货助手 ===")
    log("按 [=] 启动")
    log("按 [-] 停止")
    log("按 [ESC] 退出程序")
    
    keyboard.add_hotkey('=', start_thread)
    keyboard.add_hotkey('-', stop_thread)
    keyboard.wait('esc')