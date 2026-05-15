import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging
from pathlib import Path
import json
import os

class PomodoroClock:
    # 窗口设置
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 500

    # UI尺寸常量
    PROGRESS_BAR_LENGTH = 400
    TASK_LIST_WIDTH = 45
    TASK_LIST_HEIGHT = 5

    # 模式常量
    MODES = ["work", "short_break", "long_break"]
    MODE_LABELS = {
        "work": "工作时间",
        "short_break": "短休息",
        "long_break": "长休息"
    }

    def __init__(self, root):
        self.root = root
        self.root.title("番茄钟 - Pomodoro Clock")
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        # 默认设置
        self.default_settings = {
            "work_duration": 25,  # 工作时间（分钟）
            "short_break": 5,     # 短休息时间（分钟）
            "long_break": 15,     # 长休息时间（分钟）
            "long_break_interval": 4,  # 长休息间隔（每4个番茄钟后）
            "auto_start_break": True,  # 工作结束后自动开始休息
            "auto_start_work": True,   # 休息结束后自动开始工作
            "sound_enabled": True,     # 启用声音提醒
            "theme": "light"           # 主题模式
        }

        # 缓存计算结果
        self.durations = {
            "work": self.default_settings["work_duration"] * 60,
            "short_break": self.default_settings["short_break"] * 60,
            "long_break": self.default_settings["long_break"] * 60
        }

        # 加载设置
        self.settings = self.load_settings()
        self.update_durations()

        # 状态变量（移除冗余状态）
        self.is_running = False
        self.is_paused = False
        self.current_mode = "work"
        self.pomodoro_count = 0
        self.time_left = 0
        self.total_work_time = 0

        # 上次统计值（用于避免不必要的UI更新）
        self.last_stats = {
            "total_work_time": -1,
            "total_pomodoros": -1,
            "pomodoro_count": -1
        }

        # 设置窗口缓存
        self.settings_window = None

        # 事件处理器列表（用于清理）
        self.event_handlers = []

        # 创建界面
        self.create_widgets()
        self.update_time_display()

    def load_settings(self):
        """加载设置文件，如果文件不存在则使用默认设置"""
        settings_file = "pomodoro_settings.json"
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                return self._merge_settings(loaded)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.warning(f"无法读取设置文件 {settings_file}，使用默认设置")
            return self.default_settings

    def _merge_settings(self, loaded_settings):
        """合并加载的设置与默认设置"""
        settings = self.default_settings.copy()
        settings.update(loaded_settings)
        return settings

    def save_settings(self):
        """保存设置到后台线程，避免阻塞UI"""
        settings_file = "pomodoro_settings.json"

        def _save():
            try:
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, ensure_ascii=False, indent=2)
            except (IOError, json.JSONEncodeError) as e:
                logging.error(f"保存设置失败: {e}")

        threading.Thread(target=_save, daemon=True).start()

    def update_durations(self):
        """更新持续时间缓存"""
        self.durations = {
            "work": self.settings["work_duration"] * 60,
            "short_break": self.settings["short_break"] * 60,
            "long_break": self.settings["long_break"] * 60
        }

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_frame, text="番茄钟", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        # 时间显示框架
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=1, column=0, columnspan=2, pady=20)

        # 时间显示标签
        self.time_label = ttk.Label(time_frame, text="25:00", font=("Arial", 48))
        self.time_label.grid(row=0, column=0)

        # 模式显示
        self.mode_label = ttk.Label(time_frame, text="工作时间", font=("Arial", 16))
        self.mode_label.grid(row=1, column=0, pady=10)

        # 番茄计数器
        self.pomodoro_label = ttk.Label(time_frame, text="Pomodoros: 0", font=("Arial", 12))
        self.pomodoro_label.grid(row=2, column=0, pady=5)

        # 控制按钮框架
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=20)

        # 开始/暂停按钮
        self.start_button = ttk.Button(control_frame, text="开始", command=self.start_timer, width=10)
        self.start_button.grid(row=0, column=0, padx=5)

        # 重置按钮
        self.reset_button = ttk.Button(control_frame, text="重置", command=self.reset_timer, width=10)
        self.reset_button.grid(row=0, column=1, padx=5)

        # 设置按钮
        settings_button = ttk.Button(control_frame, text="设置", command=self.open_settings, width=10)
        settings_button.grid(row=0, column=2, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, length=self.PROGRESS_BAR_LENGTH, mode='determinate')
        self.progress.grid(row=3, column=0, columnspan=2, pady=20)

        # 统计信息框架
        stats_frame = ttk.LabelFrame(main_frame, text="今日统计", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))

        # 统计标签
        self.work_time_label = ttk.Label(stats_frame, text="总工作时间: 0 分钟", font=("Arial", 10))
        self.work_time_label.grid(row=0, column=0, sticky=tk.W, pady=2)

        self.completed_pomodoros_label = ttk.Label(stats_frame, text="完成番茄数: 0", font=("Arial", 10))
        self.completed_pomodoros_label.grid(row=1, column=0, sticky=tk.W, pady=2)

        # 任务列表
        task_frame = ttk.LabelFrame(main_frame, text="任务列表", padding="10")
        task_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 任务输入
        task_input_frame = ttk.Frame(task_frame)
        task_input_frame.grid(row=0, column=0, columnspan=2, pady=5)

        self.task_entry = ttk.Entry(task_input_frame, width=40)
        self.task_entry.grid(row=0, column=0, padx=5)
        self.task_entry.bind('<Return>', lambda e: self.add_task())

        add_task_button = ttk.Button(task_input_frame, text="添加", command=self.add_task, width=10)
        add_task_button.grid(row=0, column=1, padx=5)
        complete_task_button = ttk.Button(task_input_frame, text="标记完成", command=self.mark_task_completed, width=10)
        complete_task_button.grid(row=0, column=2, padx=5)

        # 任务列表框
        scrollbar = ttk.Scrollbar(task_frame)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        self.task_listbox = tk.Listbox(task_frame, width=self.TASK_LIST_WIDTH, height=self.TASK_LIST_HEIGHT, yscrollcommand=scrollbar.set)
        self.task_listbox.grid(row=1, column=0, pady=5)
        scrollbar.config(command=self.task_listbox.yview)

        # 保存事件处理器以便清理
        handler = lambda e: self.add_task()
        self.task_entry.bind('<Return>', handler)
        self.event_handlers.append(('task_entry', '<Return>', handler))

        # 快捷按钮
        quick_frame = ttk.Frame(main_frame)
        quick_frame.grid(row=6, column=0, columnspan=2, pady=10)

        # 快捷计时器按钮
        ttk.Button(quick_frame, text="25分钟工作", command=lambda: self.set_quick_timer("work"), width=10).grid(row=0, column=0, padx=2)
        ttk.Button(quick_frame, text="5分钟休息", command=lambda: self.set_quick_timer("short_break"), width=10).grid(row=0, column=1, padx=2)
        ttk.Button(quick_frame, text="15分钟休息", command=lambda: self.set_quick_timer("long_break"), width=10).grid(row=0, column=2, padx=2)

    def update_time_display(self):
        """更新时间显示，添加变化检测避免不必要的UI更新"""
        # 更新时间显示
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")

        # 更新进度条（仅在运行且未暂停时）
        if self.is_running and not self.is_paused:
            total_seconds = self.durations[self.current_mode]
            progress = ((total_seconds - self.time_left) / total_seconds) * 100
            self.progress['value'] = progress

        # 使用缓存的模式标签
        self.mode_label.config(text=self.MODE_LABELS[self.current_mode])

        # 更新统计（仅在值变化时）
        if (self.total_work_time != self.last_stats["total_work_time"] or
            self.pomodoro_count != self.last_stats["pomodoro_count"]):

            # 计算总完成番茄数（冗余状态移除后需要计算）
            total_pomodoros = self.pomodoro_count

            self.work_time_label.config(text=f"总工作时间: {self.total_work_time} 分钟")
            self.completed_pomodoros_label.config(text=f"完成番茄数: {total_pomodoros}")
            self.pomodoro_label.config(text=f"Pomodoros: {self.pomodoro_count}")

            # 更新缓存的统计值
            self.last_stats["total_work_time"] = self.total_work_time
            self.last_stats["pomodoro_count"] = self.pomodoro_count

    def format_time_display(self, seconds):
        """格式化时间为 MM:SS 显示"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def set_mode_and_time(self, mode):
        """通用方法：设置模式并初始化时间"""
        self.current_mode = mode
        self.time_left = self.durations[mode]

    def start_timer(self):
        """开始计时器"""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.update_button_text()

            # 如果是第一次开始或重置后，初始化时间
            if self.time_left == 0:
                self.set_mode_and_time(self.current_mode)

            # 启动计时线程
            threading.Thread(target=self.timer_thread, daemon=True).start()
        elif self.is_paused:
            # 继续计时
            self.is_paused = False
            self.update_button_text()
            threading.Thread(target=self.timer_thread, daemon=True).start()
        else:
            # 暂停计时
            self.is_paused = True
            self.update_button_text()

    def update_button_text(self):
        """更新按钮文本 - 分离UI更新逻辑"""
        self.start_button.config(text="继续" if self.is_paused else "暂停")

    def pause_timer(self):
        """暂停计时器"""
        if self.is_running:
            self.is_paused = True
            self.update_button_text()

    def pause_timer(self):
        """暂停计时器"""
        if self.is_running:
            self.is_paused = True
            self.start_button.config(text="继续")

    def reset_timer(self):
        """重置计时器"""
        self.is_running = False
        self.is_paused = False
        self.time_left = 0
        self.start_button.config(text="开始")
        self.update_time_display()
        self.progress['value'] = 0

    def timer_thread(self):
        """计时器线程"""
        while self.is_running and self.time_left > 0:
            if not self.is_paused:
                self.time_left -= 1
                self.root.after(0, self.update_time_display)
                time.sleep(1)
            else:
                # 暂停状态下，只是等待
                time.sleep(0.1)

        # 计时结束（必须在主线程里更新 UI / 弹窗）
        if self.time_left == 0 and self.is_running:
            self.root.after(0, self.timer_finished)

    def timer_finished(self):
        """计时器完成"""
        self.is_running = False
        self.update_button_text()

        # 播放提醒（模拟）
        if self.settings["sound_enabled"]:
            print("\a")  # 系统提示音

        # 使用分解的方法处理不同的完成情况
        if self.current_mode == "work":
            self._handle_work_completion()
        else:
            self._handle_break_completion()

        self._handle_auto_start()
        self.update_time_display()

    def _handle_work_completion(self):
        """处理工作完成"""
        self.pomodoro_count += 1
        self.total_work_time += self.settings["work_duration"]

        # 确定下一个模式
        if self.pomodoro_count % self.settings["long_break_interval"] == 0:
            next_mode = "long_break"
            duration = self.settings["long_break"]
            message = f"完成一个番茄钟！已连续完成 {self.pomodoro_count} 个番茄钟。\n\n该休息了！长休息 {duration} 分钟。"
        else:
            next_mode = "short_break"
            duration = self.settings["short_break"]
            message = f"完成一个番茄钟！\n\n该休息了！短休息 {duration} 分钟。"

        self.current_mode = next_mode
        messagebox.showinfo("时间到！", message)

    def _handle_break_completion(self):
        """处理休息完成"""
        self.current_mode = "work"
        messagebox.showinfo("时间到！", "休息结束！\n\n该继续工作了！")

    def _handle_auto_start(self):
        """处理自动开始下一个计时"""
        if self.current_mode == "work" and self.settings["auto_start_work"]:
            self.set_mode_and_time("work")
            self._start_timer_thread()
        elif self.current_mode != "work" and self.settings["auto_start_break"]:
            self.set_mode_and_time(self.current_mode)
            self._start_timer_thread()

    def _start_timer_thread(self):
        """启动计时线程的通用方法"""
        self.is_running = True
        self.update_button_text()
        threading.Thread(target=self.timer_thread, daemon=True).start()

    def open_settings(self):
        """打开设置窗口，缓存窗口实例避免重复创建"""
        # 如果窗口已存在且未销毁，提升窗口
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("设置")
        self.settings_window.geometry("400x500")
        self.settings_window.resizable(False, False)

        # 设置框架
        settings_frame = ttk.Frame(self.settings_window, padding="20")
        settings_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 工作时长
        ttk.Label(settings_frame, text="工作时长（分钟）:").grid(row=0, column=0, sticky=tk.W, pady=5)
        work_duration = ttk.Spinbox(settings_frame, from_=1, to=120, width=10)
        work_duration.set(self.settings["work_duration"])
        work_duration.grid(row=0, column=1, padx=10, pady=5)

        # 短休息时长
        ttk.Label(settings_frame, text="短休息时长（分钟）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        short_break = ttk.Spinbox(settings_frame, from_=1, to=30, width=10)
        short_break.set(self.settings["short_break"])
        short_break.grid(row=1, column=1, padx=10, pady=5)

        # 长休息时长
        ttk.Label(settings_frame, text="长休息时长（分钟）:").grid(row=2, column=0, sticky=tk.W, pady=5)
        long_break = ttk.Spinbox(settings_frame, from_=1, to=60, width=10)
        long_break.set(self.settings["long_break"])
        long_break.grid(row=2, column=1, padx=10, pady=5)

        # 长休息间隔
        ttk.Label(settings_frame, text="长休息间隔:").grid(row=3, column=0, sticky=tk.W, pady=5)
        long_break_interval = ttk.Spinbox(settings_frame, from_=2, to=10, width=10)
        long_break_interval.set(self.settings["long_break_interval"])
        long_break_interval.grid(row=3, column=1, padx=10, pady=5)

        # 自动开始休息
        auto_start_break = tk.BooleanVar(value=self.settings["auto_start_break"])
        ttk.Checkbutton(settings_frame, text="工作结束后自动开始休息",
                       variable=auto_start_break).grid(row=4, column=0, columnspan=2, pady=5)

        # 自动开始工作
        auto_start_work = tk.BooleanVar(value=self.settings["auto_start_work"])
        ttk.Checkbutton(settings_frame, text="休息结束后自动开始工作",
                       variable=auto_start_work).grid(row=5, column=0, columnspan=2, pady=5)

        # 声音提醒
        sound_enabled = tk.BooleanVar(value=self.settings["sound_enabled"])
        ttk.Checkbutton(settings_frame, text="启用声音提醒",
                       variable=sound_enabled).grid(row=6, column=0, columnspan=2, pady=5)

        # 主题
        ttk.Label(settings_frame, text="主题:").grid(row=7, column=0, sticky=tk.W, pady=5)
        theme_var = tk.StringVar(value=self.settings["theme"])
        ttk.Radiobutton(settings_frame, text="浅色", variable=theme_var,
                       value="light").grid(row=7, column=1, sticky=tk.W)
        ttk.Radiobutton(settings_frame, text="深色", variable=theme_var,
                       value="dark").grid(row=8, column=1, sticky=tk.W)

        # 按钮框架
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)

        def save_settings():
            """保存设置"""
            self.settings["work_duration"] = int(work_duration.get())
            self.settings["short_break"] = int(short_break.get())
            self.settings["long_break"] = int(long_break.get())
            self.settings["long_break_interval"] = int(long_break_interval.get())
            self.settings["auto_start_break"] = auto_start_break.get()
            self.settings["auto_start_work"] = auto_start_work.get()
            self.settings["sound_enabled"] = sound_enabled.get()
            self.settings["theme"] = theme_var.get()

            # 更新缓存
            self.update_durations()

            # 保存到后台线程
            self.save_settings()
            messagebox.showinfo("成功", "设置已保存！")
            self.settings_window.destroy()

        ttk.Button(button_frame, text="保存", command=save_settings, width=10).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="取消", command=self.settings_window.destroy, width=10).grid(row=0, column=1, padx=5)

    def set_quick_timer(self, mode):
        """设置快速计时器"""
        if not self.is_running:
            self.reset_timer()
            self.set_mode_and_time(mode)
            self.update_time_display()

    def add_task(self):
        """添加任务"""
        task = self.task_entry.get().strip()
        if task:
            self.task_listbox.insert(tk.END, f"[未完成] {task}")
            self.task_entry.delete(0, tk.END)

    def get_incomplete_tasks(self):
        """获取未完成任务列表"""
        incomplete = []
        for i in range(self.task_listbox.size()):
            task = self.task_listbox.get(i)
            if task.startswith("[未完成]"):
                incomplete.append((i, task))
        return incomplete

    def mark_task_completed(self):
        """标记任务完成"""
        selection = self.task_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        task = self.task_listbox.get(idx)
        if task.startswith("[未完成]"):
            completed_task = task.replace("[未完成]", "[已完成]")
            self.task_listbox.delete(idx)
            self.task_listbox.insert(tk.END, completed_task)
            # 选中新添加的任务
            last = self.task_listbox.size() - 1
            self.task_listbox.selection_set(last)

    def cleanup_event_handlers(self):
        """清理事件处理器，防止内存泄漏"""
        for widget, event, handler in self.event_handlers:
            try:
                widget.unbind(event, handler)
            except:
                pass
        self.event_handlers.clear()

def main():
        root = tk.Tk()
        app = PomodoroClock(root)

        # 绑定关闭事件
        def on_closing():
            # 清理事件处理器
            app.cleanup_event_handlers()
            if messagebox.askokcancel("退出", "确定要退出番茄钟吗？"):
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

# 主程序入口
if __name__ == "__main__":
    main()