# run.py
import sys
import os
import ctypes

if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

SRC_DIR = os.path.join(ROOT_DIR, "src")

sys.path.append(ROOT_DIR)
sys.path.append(SRC_DIR)

def show_error(msg):
    ctypes.windll.user32.MessageBoxW(0, str(msg), "启动错误", 0x10)

try:
    from src.main import App
except ImportError as e:
    show_error(f"无法导入模块。\n详细错误: {e}\n\n请检查 src 文件夹是否完整，或打包路径配置。")
    sys.exit(1)
except Exception as e:
    show_error(f"发生未知错误: {e}")
    sys.exit(1)

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        show_error(f"运行时崩溃: {e}")