# src/main.py
import customtkinter as ctk
import sys
import os
import re
import json
import threading
from tkinter import messagebox
from datetime import datetime
import keyboard
import importlib
import config
import utils
import core_logic

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.py")
LOG_DIR = os.path.join(ROOT_DIR, "logs")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        try:
            importlib.reload(config)
            print(f"配置已重载: \n最大扫描数量{config.MAX_SCAN_COUNT}\n是否启用日志:{config.LOG}\n是否启用调试模式:{config.DEBUG_MODE}\n临时文件目录:{config.TMP_DIR}\n日志文件目录:{config.LOG_DIR}")
        except Exception as e:
            print(f"配置重载失败: {e}")

        self.title("终末地倒货助手")
        self.geometry("950x700")
        
        self.stop_event = False
        self.work_thread = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.navigation_frame, text="倒卖助手",
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = self.create_nav_button("使用说明", self.home_button_event, 1)
        self.log_file_button = self.create_nav_button("历史日志", self.log_file_button_event, 2)
        self.console_button = self.create_nav_button("控制台输出", self.console_button_event, 3)
        self.settings_button = self.create_nav_button("参数设置", self.settings_button_event, 4)

        self.switch_frame = ctk.CTkFrame(self.navigation_frame)
        self.switch_frame.grid(row=6, column=0, padx=10, pady=20, sticky="s")
        
        self.btn_start = ctk.CTkButton(self.switch_frame, text="启动任务 (=)", command=self.start_task, fg_color="green")
        self.btn_start.pack(pady=5)
        
        self.btn_stop = ctk.CTkButton(self.switch_frame, text="停止任务 (-)", command=self.stop_task, fg_color="darkred")
        self.btn_stop.pack(pady=5)

        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_text = ctk.CTkTextbox(self.home_frame, font=("微软雅黑", 14))
        self.home_text.pack(expand=True, fill="both", padx=20, pady=20)
        self.home_text.insert("0.0", """【使用说明】

1. 环境准备：
   - 以管理员身份运行程序
   - 游戏分辨率不做限制，推荐1920*1080
   - 按"Y"打开地区建设 -> 物资调度 -> 弹性物资需求

2. 运行逻辑：
   - 使用 wx-ocr 识别物资名称和位置。
   - 使用 RapidOCR 识别价格、点击按钮。
   - 使用 RapidOCR 等待数据加载、识别最高价，自动计算利润。

3. 快捷键：
   - [=] 键：开始
   - [-] 键：停止
   
4. 注意：
   - 程序通过ocr进行识别，因此在部分情况下(如设备限制、网络波动等)会存在识别错误的情况
""")
        self.home_text.configure(state="disabled")

        self.log_file_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.btn_refresh_log = ctk.CTkButton(self.log_file_frame, text="刷新今日日志", command=self.read_log_file)
        self.btn_refresh_log.pack(pady=10)
        self.log_file_text = ctk.CTkTextbox(self.log_file_frame, font=("Consolas", 12))
        self.log_file_text.pack(expand=True, fill="both", padx=20, pady=(0, 20))

        self.console_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.console_text = ctk.CTkTextbox(self.console_frame, font=("Consolas", 12), text_color="#00FF00", fg_color="black")
        self.console_text.pack(expand=True, fill="both", padx=20, pady=20)

        self.settings_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        self.select_frame_by_name("home")
        
        utils.init_logger()
        utils.set_ui_callback(self.append_console)

        try:
            keyboard.add_hotkey('=', self.start_task)
            keyboard.add_hotkey('-', self.stop_task)
            self.append_console("热键注册成功 (=启动, -停止)")
        except Exception as e:
            self.append_console(f"热键注册失败: {e}")

    def create_nav_button(self, text, command, row):
        btn = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                            text=text, fg_color="transparent", text_color=("gray10", "gray90"),
                            hover_color=("gray70", "gray30"), anchor="w", command=command)
        btn.grid(row=row, column=0, sticky="ew")
        return btn

    def build_settings_ui(self):
        for widget in self.settings_frame.winfo_children():
            widget.destroy()

        top_bar = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=10)
        
        self.log_switch_var = ctk.StringVar(value="on" if getattr(config, 'LOG', True) else "off")
        self.log_switch = ctk.CTkSwitch(top_bar, text="启用日志记录", 
                                        variable=self.log_switch_var, onvalue="on", offvalue="off")
        self.log_switch.pack(side="left", padx=(0, 20))

        self.debug_switch_var = ctk.StringVar(value="on" if getattr(config, 'DEBUG_MODE', False) else "off")
        self.debug_switch = ctk.CTkSwitch(top_bar, text="调试模式", 
                                          variable=self.debug_switch_var, onvalue="on", offvalue="off")
        self.debug_switch.pack(side="left")

        self.btn_save = ctk.CTkButton(top_bar, text="保存设置并生效", fg_color="#E6A23C", text_color="black",
                                      command=self.save_config)
        self.btn_save.pack(side="right")

        setting_container = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        setting_container.pack(fill="x", padx=20, pady=20)

        lbl = ctk.CTkLabel(setting_container, text="单次扫描物品上限:", font=("微软雅黑", 14), width=150, anchor="w")
        lbl.grid(row=0, column=0, padx=10, pady=10)
        
        current_max = getattr(config, 'MAX_SCAN_COUNT', 12)
        
        self.max_scan_entry = ctk.CTkEntry(setting_container, width=100)
        self.max_scan_entry.insert(0, str(current_max))
        self.max_scan_entry.grid(row=0, column=1, padx=10, pady=10)
        
        desc = ctk.CTkLabel(setting_container, text="(扫描列表前 N 个物品后停止)", text_color="gray")
        desc.grid(row=0, column=2, padx=10)

        bottom_bar = ctk.CTkFrame(self.settings_frame, fg_color="transparent") 
        bottom_bar.pack(fill="x", padx=20, pady=20)
        note = ctk.CTkLabel(bottom_bar, text="注：调试模式开启后，会在 tmp 文件夹下保存大量截图，请定期清理。", text_color="gray")
        note.pack()

    def select_frame_by_name(self, name):
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.log_file_button.configure(fg_color=("gray75", "gray25") if name == "log_file" else "transparent")
        self.console_button.configure(fg_color=("gray75", "gray25") if name == "console" else "transparent")
        self.settings_button.configure(fg_color=("gray75", "gray25") if name == "settings" else "transparent")

        self.home_frame.grid_forget()
        self.log_file_frame.grid_forget()
        self.console_frame.grid_forget()
        self.settings_frame.grid_forget()

        if name == "home": self.home_frame.grid(row=0, column=1, sticky="nsew")
        if name == "log_file": 
            self.log_file_frame.grid(row=0, column=1, sticky="nsew")
            self.read_log_file()
        if name == "console": self.console_frame.grid(row=0, column=1, sticky="nsew")
        if name == "settings": 
            self.build_settings_ui()
            self.settings_frame.grid(row=0, column=1, sticky="nsew")

    def settings_button_event(self): self.select_frame_by_name("settings")
    def home_button_event(self): self.select_frame_by_name("home")
    def log_file_button_event(self): self.select_frame_by_name("log_file")
    def console_button_event(self): self.select_frame_by_name("console")

    def worker(self):
        try:
            core_logic.run_job(lambda: self.stop_event)
        except Exception as e:
            self.append_console(f"运行时发生未捕获异常: {e}")
        finally:
            self.stop_event = False
            self.append_console(">>> 线程已结束")

    def start_task(self):
        if self.work_thread and self.work_thread.is_alive():
            self.append_console("任务已在运行中...")
            return
        
        self.append_console(">>> UI 指令: 启动任务")
        self.stop_event = False
        self.work_thread = threading.Thread(target=self.worker, daemon=True)
        self.work_thread.start()
        
    def stop_task(self):
        if self.work_thread and self.work_thread.is_alive():
            self.append_console(">>> UI 指令: 请求停止...")
            self.stop_event = True
        else:
            self.append_console("当前没有任务在运行")

    def append_console(self, msg):
        def _update():
            self.console_text.insert("end", str(msg) + "\n")
            self.console_text.see("end")
        self.after(0, _update)

    def read_log_file(self):
        filename = f"log_{datetime.now().strftime('%Y-%m-%d')}.txt"
        filepath = os.path.join(LOG_DIR, filename)
        
        self.log_file_text.delete("0.0", "end")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.log_file_text.insert("0.0", f.read())
            except Exception as e:
                self.log_file_text.insert("0.0", f"读取失败: {e}")
        else:
            self.log_file_text.insert("0.0", f"今日无日志文件。\n路径: {filepath}")

    def save_config(self):
        try:
            new_log_state = True if self.log_switch_var.get() == "on" else False
            new_debug_state = True if self.debug_switch_var.get() == "on" else False
            try:
                new_max_count = int(self.max_scan_entry.get())
                if new_max_count <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("错误", "扫描上限必须是大于0的整数")
                return
            config.LOG = new_log_state
            config.DEBUG_MODE = new_debug_state
            config.MAX_SCAN_COUNT = new_max_count

            new_content = f'''# -*- coding: utf-8 -*-

GAME_WINDOW_TITLE = "{getattr(config, 'GAME_WINDOW_TITLE', 'Endfield')}"
LOG = {new_log_state}
DEBUG_MODE = {new_debug_state}

TMP_DIR = "{getattr(config, 'TMP_DIR', 'tmp')}"
LOG_DIR = "{getattr(config, 'LOG_DIR', 'logs')}"

# 单次扫描物品数量上限
MAX_SCAN_COUNT = {new_max_count}
'''

            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            utils.init_logger()

            messagebox.showinfo("成功", "设置已保存并生效")
            self.append_console(f"配置已更新: 上限{new_max_count}, 调试{'开' if new_debug_state else '关'}")

        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            self.append_console(f"保存配置出错: {e}")