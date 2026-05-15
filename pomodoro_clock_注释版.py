import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, timedelta
import json
import os

class PomodoroClock:
    def __init__(self, root):
        # 初始化主窗口
        self.root = root
        self.root.title("番茄钟 - Pomodoro Clock")
        self.root.geometry("600x500")  # 窗口大小
        self.root.resizable(False, False)  # 禁止调整窗口大小

        # 【默认设置】- 番茄钟的工作参数
        self.default_settings = {
            "work_duration": 25,        # 工作时长（分钟）
            "short_break": 5,           # 短休息时长（分钟）
            "long_break": 15,           # 长休息时长（分钟）
            "long_break_interval": 4,    # 长休息间隔（每4个番茄钟后）
            "auto_start_break": True,    # 工作结束后自动开始休息
            "auto_start_work": True,     # 休息结束后自动开始工作
            "sound_enabled": True,       # 启用声音提醒
            "theme": "light"             # 主题模式（浅色/深色）
        }

        # 【加载设置】- 从配置文件读取用户设置，如果不存在则使用默认值
        self.settings = self.load_settings()

        # 【状态变量】- 记录番茄钟的当前状态
        self.is_running = False      # 是否正在计时
        self.is_paused = False        # 是否处于暂停状态
        self.current_mode = "work"    # 当前模式：工作、短休息、长休息
        self.pomodoro_count = 0      # 当前番茄钟计数（用于计算长休息）
        self.time_left = 0           # 剩余时间（秒）
        self.total_work_time = 0     # 今日总工作时间（分钟）
        self.total_pomodoros = 0     # 今日总完成番茄数

        # 【创建界面】- 构建图形用户界面
        self.create_widgets()
        # 【更新显示】- 初始化界面显示
        self.update_time_display()

    def load_settings(self):
        """
        【加载设置文件】
        从JSON文件读取用户自定义设置
        如果文件不存在或读取失败，返回默认设置
        """
        settings_file = "pomodoro_settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 合并默认设置，确保所有设置项都存在
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
            except:
                # 如果读取失败，返回默认设置
                return self.default_settings
        return self.default_settings

    def save_settings(self):
        """
        【保存设置】
        将当前设置保存到JSON文件中
        设置持久化，下次启动时可以恢复
        """
        settings_file = "pomodoro_settings.json"
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except:
            # 如果保存失败，静默忽略
            pass

    def create_widgets(self):
        """
        【创建界面组件】
        构建整个应用的图形界面，包括所有控件和布局
        """
        # 【主框架】- 所有界面组件的容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 【标题】- 显示应用名称
        title_label = ttk.Label(main_frame, text="番茄钟", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # 【时间显示框架】- 用于显示计时信息
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=1, column=0, columnspan=2, pady=20)

        # 【时间显示】- 大字体显示剩余时间
        self.time_label = ttk.Label(time_frame, text="25:00", font=("Arial", 48))
        self.time_label.grid(row=0, column=0)

        # 【模式显示】- 显示当前是工作时间还是休息时间
        self.mode_label = ttk.Label(time_frame, text="工作时间", font=("Arial", 16))
        self.mode_label.grid(row=1, column=0, pady=10)

        # 【番茄计数器】- 显示已完成的番茄数
        self.pomodoro_label = ttk.Label(time_frame, text="Pomodoros: 0", font=("Arial", 12))
        self.pomodoro_label.grid(row=2, column=0, pady=5)

        # 【控制按钮框架】- 包含开始、暂停、重置等按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=20)

        # 【开始/暂停按钮】- 控制计时器的启停
        self.start_button = ttk.Button(control_frame, text="开始", command=self.start_timer, width=10)
        self.start_button.grid(row=0, column=0, padx=5)

        # 【重置按钮】- 重置计时器到初始状态
        self.reset_button = ttk.Button(control_frame, text="重置", command=self.reset_timer, width=10)
        self.reset_button.grid(row=0, column=1, padx=5)

        # 【设置按钮】- 打开设置窗口
        settings_button = ttk.Button(control_frame, text="设置", command=self.open_settings, width=10)
        settings_button.grid(row=0, column=2, padx=5)

        # 【进度条】- 可视化显示计时进度
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=2, pady=20)

        # 【统计信息框架】- 显示今日统计
        stats_frame = ttk.LabelFrame(main_frame, text="今日统计", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))

        # 【工作时长统计】- 显示累计工作时间
        self.work_time_label = ttk.Label(stats_frame, text="总工作时间: 0 分钟", font=("Arial", 10))
        self.work_time_label.grid(row=0, column=0, sticky=tk.W, pady=2)

        # 【完成番茄数统计】- 显示完成的番茄钟数量
        self.completed_pomodoros_label = ttk.Label(stats_frame, text="完成番茄数: 0", font=("Arial", 10))
        self.completed_pomodoros_label.grid(row=1, column=0, sticky=tk.W, pady=2)

        # 【任务列表框架】- 任务管理区域
        task_frame = ttk.LabelFrame(main_frame, text="任务列表", padding="10")
        task_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 【任务输入区域】- 添加新任务
        task_input_frame = ttk.Frame(task_frame)
        task_input_frame.grid(row=0, column=0, columnspan=2, pady=5)

        # 【任务输入框】- 输入任务内容
        self.task_entry = ttk.Entry(task_input_frame, width=40)
        self.task_entry.grid(row=0, column=0, padx=5)
        # 【回车键绑定】- 按回车键也可以添加任务
        self.task_entry.bind('<Return>', lambda e: self.add_task())

        # 【添加任务按钮】- 将任务添加到列表
        add_task_button = ttk.Button(task_input_frame, text="添加", command=self.add_task, width=10)
        add_task_button.grid(row=0, column=1, padx=5)

        # 【标记完成按钮】- 将选中的任务标记为已完成
        complete_task_button = ttk.Button(task_input_frame, text="标记完成", command=self.mark_task_completed, width=10)
        complete_task_button.grid(row=0, column=2, padx=5)

        # 【任务列表滚动条】- 支持滚动查看任务
        scrollbar = ttk.Scrollbar(task_frame)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        # 【任务列表】- 显示所有任务
        self.task_listbox = tk.Listbox(task_frame, width=45, height=5, yscrollcommand=scrollbar.set)
        self.task_listbox.grid(row=1, column=0, pady=5)
        scrollbar.config(command=self.task_listbox.yview)

        # 【快捷按钮框架】- 快速切换模式
        quick_frame = ttk.Frame(main_frame)
        quick_frame.grid(row=6, column=0, columnspan=2, pady=10)

        # 【快捷计时器按钮】- 快速设置不同时间模式
        ttk.Button(quick_frame, text="25分钟工作", command=lambda: self.set_quick_timer("work"), width=10).grid(row=0, column=0, padx=2)
        ttk.Button(quick_frame, text="5分钟休息", command=lambda: self.set_quick_timer("short_break"), width=10).grid(row=0, column=1, padx=2)
        ttk.Button(quick_frame, text="15分钟休息", command=lambda: self.set_quick_timer("long_break"), width=10).grid(row=0, column=2, padx=2)

    def update_time_display(self):
        """
        【更新时间显示】
        更新界面上的时间显示、进度条和统计信息
        """
        # 【计算分钟和秒】- 将剩余秒数转换为分:秒格式
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")

        # 【更新进度条】- 显示当前计时的进度百分比
        if self.is_running and not self.is_paused:
            # 根据当前模式计算总时间
            if self.current_mode == "work":
                total_seconds = self.settings["work_duration"] * 60
            elif self.current_mode == "short_break":
                total_seconds = self.settings["short_break"] * 60
            else:
                total_seconds = self.settings["long_break"] * 60

            # 计算进度百分比
            progress = ((total_seconds - self.time_left) / total_seconds) * 100
            self.progress['value'] = progress

        # 【更新模式显示】- 根据当前模式更新模式文字
        if self.current_mode == "work":
            self.mode_label.config(text="工作时间")
        elif self.current_mode == "short_break":
            self.mode_label.config(text="短休息")
        else:
            self.mode_label.config(text="长休息")

        # 【更新统计信息】- 刷新统计数据
        self.work_time_label.config(text=f"总工作时间: {self.total_work_time} 分钟")
        self.completed_pomodoros_label.config(text=f"完成番茄数: {self.total_pomodoros}")
        self.pomodoro_label.config(text=f"Pomodoros: {self.pomodoro_count}")

    def start_timer(self):
        """
        【开始计时器】
        控制计时器的开始、暂停和继续
        """
        if not self.is_running:
            # 【启动计时】- 计时器从未开始状态启动
            self.is_running = True
            self.is_paused = False
            self.start_button.config(text="暂停")

            # 【初始化时间】- 如果是首次开始，设置对应时间
            if self.time_left == 0:
                if self.current_mode == "work":
                    self.time_left = self.settings["work_duration"] * 60
                elif self.current_mode == "short_break":
                    self.time_left = self.settings["short_break"] * 60
                else:
                    self.time_left = self.settings["long_break"] * 60

            # 【启动计时线程】- 在独立线程中运行计时器
            threading.Thread(target=self.timer_thread, daemon=True).start()
        elif self.is_paused:
            # 【继续计时】- 从暂停状态恢复
            self.is_paused = False
            self.start_button.config(text="暂停")
            threading.Thread(target=self.timer_thread, daemon=True).start()
        else:
            # 【暂停计时】- 暂停当前计时
            self.is_paused = True
            self.start_button.config(text="继续")

    def pause_timer(self):
        """
        【暂停计时器】
        暂停当前计时器的运行
        """
        if self.is_running:
            self.is_paused = True
            self.start_button.config(text="继续")

    def reset_timer(self):
        """
        【重置计时器】
        将计时器重置到初始状态
        """
        self.is_running = False
        self.is_paused = False
        self.time_left = 0
        self.start_button.config(text="开始")
        self.update_time_display()
        self.progress['value'] = 0

    def timer_thread(self):
        """
        【计时器线程】
        在后台线程中执行计时逻辑，每秒更新一次显示
        使用 daemon=True 确保程序退出时线程自动结束
        """
        while self.is_running and self.time_left > 0:
            if not self.is_paused:
                # 【倒计时】- 每秒减少1秒
                self.time_left -= 1
                # 【更新界面】- 在主线程中更新显示
                self.root.after(0, self.update_time_display)
                # 【等待1秒】- 使用time.sleep实现1秒间隔
                time.sleep(1)
            else:
                # 【暂停等待】- 暂停状态下只是空循环
                time.sleep(0.1)

        # 【计时结束检查】- 当时间归零时处理
        if self.time_left == 0 and self.is_running:
            self.timer_finished()

    def timer_finished(self):
        """
        【计时完成处理】
        当计时器归零时，进行相应的处理
        """
        self.is_running = False
        self.start_button.config(text="开始")

        # 【播放提醒】- 如果启用声音提醒，播放系统提示音
        if self.settings["sound_enabled"]:
            print("\a")  # 使用ASCII铃声字符

        # 【模式判断】- 根据当前模式决定下一步动作
        if self.current_mode == "work":
            # 【工作完成】- 记录完成的工作时间
            self.pomodoro_count += 1
            self.total_pomodoros += 1
            self.total_work_time += self.settings["work_duration"]

            # 【长休息判断】- 检查是否需要长休息
            if self.pomodoro_count % self.settings["long_break_interval"] == 0:
                self.current_mode = "long_break"
                messagebox.showinfo("时间到！", f"完成一个番茄钟！已连续完成 {self.pomodoro_count} 个番茄钟。\n\n该休息了！长休息 15 分钟。")
            else:
                self.current_mode = "short_break"
                messagebox.showinfo("时间到！", f"完成一个番茄钟！\n\n该休息了！短休息 5 分钟。")
        else:
            # 【休息结束】- 准备进入下一轮工作
            self.current_mode = "work"
            messagebox.showinfo("时间到！", "休息结束！\n\n该继续工作了！")

        # 【自动开始】- 根据设置自动开始下一个计时
        if self.settings["auto_start_break"] and self.current_mode != "work":
            self.time_left = self.settings[self.current_mode + "_time"] * 60 if self.current_mode == "short_break" else self.settings["long_break"] * 60
            self.is_running = True
            threading.Thread(target=self.timer_thread, daemon=True).start()
        elif self.settings["auto_start_work"] and self.current_mode == "work":
            self.time_left = self.settings["work_duration"] * 60
            self.is_running = True
            threading.Thread(target=self.timer_thread, daemon=True).start()

        # 【更新界面】- 刷新显示信息
        self.update_time_display()

    def open_settings(self):
        """
        【打开设置窗口】
        创建并显示设置对话框，允许用户自定义各种参数
        """
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x500")
        settings_window.resizable(False, False)

        # 【设置框架】- 设置窗口的主容器
        settings_frame = ttk.Frame(settings_window, padding="20")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 【工作时长设置】- 1-120分钟可调
        ttk.Label(settings_frame, text="工作时长（分钟）:").grid(row=0, column=0, sticky=tk.W, pady=5)
        work_duration = ttk.Spinbox(settings_frame, from_=1, to=120, width=10)
        work_duration.set(self.settings["work_duration"])
        work_duration.grid(row=0, column=1, padx=10, pady=5)

        # 【短休息设置】- 1-30分钟可调
        ttk.Label(settings_frame, text="短休息时长（分钟）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        short_break = ttk.Spinbox(settings_frame, from_=1, to=30, width=10)
        short_break.set(self.settings["short_break"])
        short_break.grid(row=1, column=1, padx=10, pady=5)

        # 【长休息设置】- 1-60分钟可调
        ttk.Label(settings_frame, text="长休息时长（分钟）:").grid(row=2, column=0, sticky=tk.W, pady=5)
        long_break = ttk.Spinbox(settings_frame, from_=1, to=60, width=10)
        long_break.set(self.settings["long_break"])
        long_break.grid(row=2, column=1, padx=10, pady=5)

        # 【长休息间隔】- 2-10个番茄钟可调
        ttk.Label(settings_frame, text="长休息间隔:").grid(row=3, column=0, sticky=tk.W, pady=5)
        long_break_interval = ttk.Spinbox(settings_frame, from_=2, to=10, width=10)
        long_break_interval.set(self.settings["long_break_interval"])
        long_break_interval.grid(row=3, column=1, padx=10, pady=5)

        # 【自动开始休息】- 复选框控制
        auto_start_break = tk.BooleanVar(value=self.settings["auto_start_break"])
        ttk.Checkbutton(settings_frame, text="工作结束后自动开始休息",
                       variable=auto_start_break).grid(row=4, column=0, columnspan=2, pady=5)

        # 【自动开始工作】- 复选框控制
        auto_start_work = tk.BooleanVar(value=self.settings["auto_start_work"])
        ttk.Checkbutton(settings_frame, text="休息结束后自动开始工作",
                       variable=auto_start_work).grid(row=5, column=0, columnspan=2, pady=5)

        # 【声音提醒】- 复选框控制
        sound_enabled = tk.BooleanVar(value=self.settings["sound_enabled"])
        ttk.Checkbutton(settings_frame, text="启用声音提醒",
                       variable=sound_enabled).grid(row=6, column=0, columnspan=2, pady=5)

        # 【主题选择】- 单选按钮组
        ttk.Label(settings_frame, text="主题:").grid(row=7, column=0, sticky=tk.W, pady=5)
        theme_var = tk.StringVar(value=self.settings["theme"])
        ttk.Radiobutton(settings_frame, text="浅色", variable=theme_var,
                       value="light").grid(row=7, column=1, sticky=tk.W)
        ttk.Radiobutton(settings_frame, text="深色", variable=theme_var,
                       value="dark").grid(row=8, column=1, sticky=tk.W)

        # 【按钮框架】- 保存和取消按钮
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)

        def save_settings():
            """
            【保存设置回调】
            将用户输入的设置保存到类变量和配置文件中
            """
            # 【更新设置】- 收集所有控件的新值
            self.settings["work_duration"] = int(work_duration.get())
            self.settings["short_break"] = int(short_break.get())
            self.settings["long_break"] = int(long_break.get())
            self.settings["long_break_interval"] = int(long_break_interval.get())
            self.settings["auto_start_break"] = auto_start_break.get()
            self.settings["auto_start_work"] = auto_start_work.get()
            self.settings["sound_enabled"] = sound_enabled.get()
            self.settings["theme"] = theme_var.get()

            # 【持久化设置】- 保存到配置文件
            self.save_settings()
            messagebox.showinfo("成功", "设置已保存！")
            settings_window.destroy()

        # 【保存按钮】- 保存设置并关闭窗口
        ttk.Button(button_frame, text="保存", command=save_settings, width=10).grid(row=0, column=0, padx=5)
        # 【取消按钮】- 关闭设置窗口，不保存更改
        ttk.Button(button_frame, text="取消", command=settings_window.destroy, width=10).grid(row=0, column=1, padx=5)

    def set_quick_timer(self, mode):
        """
        【设置快速计时器】
        快速切换到指定的时间模式

        Args:
            mode (str): 时间模式 - "work"、"short_break"、"long_break"
        """
        if not self.is_running:
            self.reset_timer()
            self.current_mode = mode
            # 【根据模式设置时间】- 将不同模式的时间转换为秒数
            if mode == "work":
                self.time_left = self.settings["work_duration"] * 60
            elif mode == "short_break":
                self.time_left = self.settings["short_break"] * 60
            else:
                self.time_left = self.settings["long_break"] * 60
            self.update_time_display()

    def add_task(self):
        """
        【添加任务】
        将任务输入框中的内容添加到任务列表
        """
        # 【获取任务内容】- 从输入框读取任务文本
        task = self.task_entry.get().strip()
        if task:
            # 【添加到列表】- 在任务列表末尾添加新任务
            self.task_listbox.insert(tk.END, f"[未完成] {task}")
            # 【清空输入】- 添加完成后清空输入框
            self.task_entry.delete(0, tk.END)

    def mark_task_completed(self):
        """
        【标记任务完成】
        将选中的任务标记为已完成状态
        """
        # 【获取选中项】- 获取用户在列表中选择的任务索引
        selection = self.task_listbox.curselection()
        if selection:
            task = self.task_listbox.get(selection)
            # 【更新状态】- 将"未完成"改为"已完成"
            if task.startswith("[未完成]"):
                completed_task = task.replace("[未完成]", "[已完成]")
                self.task_listbox.delete(selection)
                self.task_listbox.insert(tk.END, completed_task)
                # 【选中新项】- 自动选中新添加的已完成任务
                self.task_listbox.selection_set(tk.END)

def main():
    """
    【主程序入口】
    创建Tkinter窗口并启动番茄钟应用
    """
    # 【创建主窗口】- 创建Tkinter根窗口
    root = tk.Tk()
    # 【创建应用实例】- 初始化番茄钟主类
    app = PomodoroClock(root)

    # 【绑定关闭事件】- 处理窗口关闭事件
    def on_closing():
        """
        【窗口关闭回调】
        确认用户是否要退出程序
        """
        if messagebox.askokcancel("退出", "确定要退出番茄钟吗？"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    # 【启动主循环】- 启动Tkinter事件循环
    root.mainloop()

if __name__ == "__main__":
    main()