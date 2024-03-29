import os
import subprocess
import threading
from tkinter import messagebox  # 从tkinter模块中导入messagebox，用于显示消息框。
import tkinter as tk


class Hexo:
    def __init__(self, root, hexo_folder_root_path, fifo_queue):
        self.root = root  # 放tk父控件
        self.process = None  # 初始化进程变量为None。
        self.root_folder = hexo_folder_root_path
        self.running = False
        self.serverunning = False
        self.task = ""
        self.task_status = ""
        self.hexo_console_text = None
        self.fifoqueue = fifo_queue

    def cmd_run(self, command="hexo", mid_do='', final_do=''):
        stderr = None
        path = self.root_folder
        self.process = subprocess.Popen(["cmd", "/c", command], cwd=path, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
        self.task = str(command)
        while True:
            output = self.process.stdout.readline().decode('utf-8', 'ignore')
            if not output:
                break
            self.fifoqueue.put(output)
        try:
            if mid_do != '':
                exec(mid_do)
            self.process.wait()
            stdout, stderr = self.process.communicate()
            self.task_status = "Done"
        except KeyboardInterrupt:
            self.process.terminate()
            messagebox.showinfo("err", "程序终止" + str(stderr))
        finally:
            if final_do != '':  # 如果最后一个执行的命令是hexo s，则打开浏览器
                exec(final_do)
            self.process = None
            self.running = False

    def set_server_running(self, boolean):
        self.serverunning = boolean

    def server(self):
        try:
            self.kill_process_on_port()
            if not self.running:
                self.running = True
                threading.Thread(target=lambda: self.cmd_run("hexo s -p 4000")).start()
                self.serverunning = True
            else:
                self.stop_s()
                messagebox.showinfo("提示", '请等待上一个进程完成！')
        except KeyboardInterrupt:
            self.process.terminate()
            self.serverunning = False
            pass

    def stop_s(self):
        if self.running:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], shell=True)
                # self.process.terminate()
            else:
                self.process.terminate()
            self.serverunning = False
            self.task = "stop"
        self.kill_process_on_port()

    def domore(self, command, mid_do='', final_do=''):
        if not self.running:
            self.running = True
            threading.Thread(target=lambda: self.cmd_run(command, mid_do, final_do)).start()
        else:
            messagebox.showinfo("提示", '请等待上一个进程完成！')
            pass

    def kill_process_on_port(self,port=4000):
        # 查找监听指定端口的PID
        result = subprocess.run(['netstat', '-aon'], capture_output=True, text=True)
        lines = result.stdout.split("\n")
        pid = None
        for line in lines:
            if f":{port}" in line and "LISTENING" in line:
                parts = line.rsplit(None, 1)
                pid = parts[-1]
                break

        # 如果找到PID，则尝试杀掉该进程
        if pid is not None:
            print(f"Port {port} is being used by PID {pid}, attempting to kill.")
            try:
                subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
                print(f"Process {pid} has been killed.")
            except Exception as e:
                print(f"Failed to kill process {pid}: {e}")
        else:
            print(f"No process is listening on port {port}.")

class TooltipButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self.show_tooltip)
        self.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        tooltip_text = self.cget("text")

        if tooltip_text:
            x = self.winfo_pointerx() + 20
            y = self.winfo_pointery() - 10

            # 创建ToolTip窗口
            self.tooltip = tk.Toplevel()

            # 确保ToolTip不会被任务栏/Alt+Tab捕获
            self.tooltip.wm_overrideredirect(True)

            # 设置ToolTip位置
            self.tooltip.wm_geometry(f"+{x}+{y}")

            label = tk.Label(self.tooltip, text=tooltip_text,
                             justify='left', background="#ffffe0",
                             relief='solid', borderwidth=1,
                             font=("Arial", "8", "normal"))

            label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()


class Loading_ui:
    def close_popup(self):
        self.popup.withdraw()
        self.popup.grab_release()

    def show_popup(self, msg, allow_close=True, withdraw=True, duration=500):
        if allow_close:
            self.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        else:
            self.popup.protocol("WM_DELETE_WINDOW", lambda: None)

        self.popup.deiconify()
        # self.popup.grab_set()
        self.message_label.configure(text=msg)
        self.popup.lift()
        if withdraw:
            self.popup.after(duration, self.close_popup)
        else:
            pass

    def __init__(self, parent):
        self.popup = tk.Toplevel(parent)
        self.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        self.popup.title("message")
        self.popup.transient(parent)  # 将窗口声明为临时窗口，不在任务栏显示图标
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        x = (screen_width / 2) - (200 / 2)
        y = (screen_height / 2) - (100 / 2)
        self.popup.geometry(f"200x100+{int(x)}+{int(y)}")
        self.message_label = tk.Label(self.popup, wraplength=180)
        self.message_label.pack(expand=True)
        self.popup.withdraw()
