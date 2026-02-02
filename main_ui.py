import customtkinter as ctk
import sys
import os
import re
import json
from tkinter import messagebox
import config
import main
import utils 
from datetime import datetime
import keyboard

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
    
CONFIG_PATH = os.path.join(get_app_path(), "config.py")

def load_external_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"外部配置文件不存在: {CONFIG_PATH}，将使用默认配置")
        return

    try:
        import importlib
        importlib.reload(config)
        print("已刷新配置")
    except Exception as e:
        print(f"加载外部配置失败: {e}")
        
class App(ctk.CTk):
    def __init__(self):
        load_external_config() 
        super().__init__()

        self.title("终末地倒货助手")
        self.geometry("950x700")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.navigation_frame, text="倒卖助手",
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                         text="使用说明", fg_color="transparent", text_color=("gray10", "gray90"),
                                         hover_color=("gray70", "gray30"), anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.log_file_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                             text="历史日志", fg_color="transparent", text_color=("gray10", "gray90"),
                                             hover_color=("gray70", "gray30"), anchor="w", command=self.log_file_button_event)
        self.log_file_button.grid(row=2, column=0, sticky="ew")

        self.console_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                            text="控制台输出", fg_color="transparent", text_color=("gray10", "gray90"),
                                            hover_color=("gray70", "gray30"), anchor="w", command=self.console_button_event)
        self.console_button.grid(row=3, column=0, sticky="ew")

        self.settings_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10,
                                             text="参数设置", fg_color="transparent", text_color=("gray10", "gray90"),
                                             hover_color=("gray70", "gray30"), anchor="w", command=self.settings_button_event)
        self.settings_button.grid(row=4, column=0, sticky="ew")

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
   - 以【管理员身份】运行本程序。
   - 游戏分辨率建议: 1920*1080 (全屏或无边框窗口)
   - 确保 img/zones 和 img/ui 下的图片完整。
   - 按"Y"打开地区建设 -> 物资调度 -> 弹性物资需求。

2. 设置功能：
   - 在“参数设置”页面可以调整各个地区的扫描数量
   - 程序会自动读取 config.py 中的 marker 图片配置，请勿随意删除文件。

3. 快捷键：
   - [=] 键：开始
   - [-] 键：停止
""")
        self.home_text.configure(state="disabled")

        self.log_file_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.btn_refresh_log = ctk.CTkButton(self.log_file_frame, text="刷新日志", command=self.read_log_file)
        self.btn_refresh_log.pack(pady=10)
        self.log_file_text = ctk.CTkTextbox(self.log_file_frame, font=("Consolas", 12))
        self.log_file_text.pack(expand=True, fill="both", padx=20, pady=(0, 20))

        self.console_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.console_text = ctk.CTkTextbox(self.console_frame, font=("Consolas", 12), text_color="#00FF00", fg_color="black")
        self.console_text.pack(expand=True, fill="both", padx=20, pady=20)

        self.settings_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.build_settings_ui()

        self.select_frame_by_name("home")
        
        utils.init_logger()
        utils.set_ui_callback(self.append_console)

        try:
            keyboard.add_hotkey('=', self.start_task)
            keyboard.add_hotkey('-', self.stop_task)
            print("热键注册成功")
        except Exception as e:
            print(f"热键注册失败: {e}")

    
    def build_settings_ui(self):
        for widget in self.settings_frame.winfo_children():
            widget.destroy()

        top_bar = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=10)
        
        self.log_switch_var = ctk.StringVar(value="on" if config.LOG else "off")
        self.log_switch = ctk.CTkSwitch(top_bar, text="启用日志记录 (写入文件)", 
                                        variable=self.log_switch_var, onvalue="on", offvalue="off")
        self.log_switch.pack(side="left")

        self.btn_save = ctk.CTkButton(top_bar, text="保存设置并生效", fg_color="#E6A23C", text_color="black",
                                      command=self.save_config)
        self.btn_save.pack(side="right")

        list_label = ctk.CTkLabel(self.settings_frame, text="地区扫描数量设置 (仅修改数量)", font=("微软雅黑", 16, "bold"), anchor="w")
        list_label.pack(fill="x", padx=20, pady=(10, 5))

        self.scroll_frame = ctk.CTkScrollableFrame(self.settings_frame, label_text="地区列表")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.region_entries = {}

        row = 0
        for region_key, data in config.REGION_DATA.items():
            lbl = ctk.CTkLabel(self.scroll_frame, text=f"{region_key}:", width=150, anchor="w")
            lbl.grid(row=row, column=0, padx=10, pady=5)
            
            current_count = 0
            if isinstance(data, int):
                current_count = data 
            elif isinstance(data, dict):
                current_count = data.get("count", 0)
            
            entry = ctk.CTkEntry(self.scroll_frame, width=100)
            entry.insert(0, str(current_count))
            entry.grid(row=row, column=1, padx=10, pady=5)
            
            self.region_entries[region_key] = entry
            row += 1

        bottom_bar = ctk.CTkFrame(self.settings_frame, fg_color="#2B2B2B") 
        bottom_bar.pack(fill="x", padx=20, pady=20)
        
        clean_label = ctk.CTkLabel(bottom_bar, text="维护工具：", font=("微软雅黑", 14, "bold"))
        clean_label.pack(side="left", padx=20, pady=20)
        
        self.btn_clean = ctk.CTkButton(bottom_bar, text="清除所有未知图片", fg_color="#F56C6C", 
                                       command=self.clear_unknowns)
        self.btn_clean.pack(side="left", padx=10)


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

    def settings_button_event(self):
        self.select_frame_by_name("settings")
    
    def home_button_event(self): self.select_frame_by_name("home")
    def log_file_button_event(self): self.select_frame_by_name("log_file")
    def console_button_event(self): self.select_frame_by_name("console")

    def start_task(self):
        self.append_console(">>> UI 指令: 启动任务")
        main.start_thread()
        
    def stop_task(self):
        self.append_console(">>> UI 指令: 停止任务")
        main.stop_thread()

    def append_console(self, msg):
        def _update():
            self.console_text.insert("end", str(msg) + "\n")
            self.console_text.see("end")
        self.after(0, _update)

    def read_log_file(self):
        log_filename = f"log_{datetime.now().strftime('%Y-%m-%d')}.txt"
        self.log_file_text.delete("0.0", "end")
        if os.path.exists(log_filename):
            try:
                with open(log_filename, "r", encoding="utf-8") as f:
                    self.log_file_text.insert("0.0", f.read())
            except: self.log_file_text.insert("0.0", "读取失败")
        else:
            self.log_file_text.insert("0.0", "今日无日志。")

    def save_config(self):
        try:
            new_log_state = True if self.log_switch_var.get() == "on" else False
            
            current_data = config.REGION_DATA.copy()
            
            for key, entry in self.region_entries.items():
                try:
                    new_count = int(entry.get())
                    
                    if key in current_data:
                        if isinstance(current_data[key], dict):
                            current_data[key]["count"] = new_count
                        else:
                            current_data[key] = {
                                "count": new_count, 
                                "marker": "", 
                                "y_filter": 0
                            }
                except ValueError:
                    messagebox.showerror("错误", f"地区 {key} 的数量必须是数字")
                    return

            with open("config.py", "r", encoding="utf-8") as f:
                content = f.read()

            content = re.sub(r"LOG\s*=\s*(True|False)", f"LOG = {new_log_state}", content)
            dict_str = "REGION_DATA = {\n"
            for k, v in current_data.items():
                val_str = json.dumps(v, ensure_ascii=False)
                dict_str += f'    "{k}": {val_str},\n'
            dict_str += "}"
            content = re.sub(r"REGION_DATA\s*=\s*\{[\s\S]*?\}", dict_str, content)

            with open("config.py", "w", encoding="utf-8") as f:
                f.write(content)

            config.LOG = new_log_state
            config.REGION_DATA = current_data
            
            utils.init_logger()

            messagebox.showinfo("成功", "设置已保存并生效")
            self.append_console(f"配置更新完毕.")

        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            self.append_console(f"保存配置出错: {e}")

    def clear_unknowns(self):
        if not messagebox.askyesno("确认", "确定要删除 img/names 下所有以 unknown 开头的图片吗？"):
            return

        base_folder = "img/names"
        deleted_count = 0
        
        try:
            for root, dirs, files in os.walk(base_folder, topdown=False):
                for name in files:
                    if name.startswith("unknown_"):
                        os.remove(os.path.join(root, name))
                        deleted_count += 1
            
            messagebox.showinfo("完成", f"清理完成，共删除了 {deleted_count} 个项目。")
            self.append_console(f"执行: 清理了 {deleted_count} 个未知项目。")
            
        except Exception as e:
            messagebox.showerror("错误", f"清理过程中出错: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()