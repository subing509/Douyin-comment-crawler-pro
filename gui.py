# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import subprocess, os, sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_cmd(cmd):
    """执行命令并返回输出"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return r.stdout + r.stderr
    except Exception as e:
        return str(e)

def login():
    """人工扫码登录"""
    profile = os.path.join(BASE_DIR, "douyin_profile")
    cmd = f"python3 crawler.py --init --profile '{profile}'"
    messagebox.showinfo("登录", "请在弹出的浏览器中扫码登录抖音，登录完成后可关闭浏览器。")
    run_cmd(cmd)
    messagebox.showinfo("完成", "登录完成，可关闭浏览器。")

def collect():
    """采集视频评论"""
    url = url_var.get().strip()
    profile = os.path.join(BASE_DIR, "douyin_profile")
    outputs_dir = os.path.join(BASE_DIR, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    # ✅ 如果没有输入链接，则自动读取 urls.txt
    urls = []
    if url:
        urls = [url]
    else:
        urls_path = os.path.join(BASE_DIR, "urls.txt")
        if os.path.exists(urls_path):
            with open(urls_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
        else:
            messagebox.showerror("错误", "未检测到视频链接，也没有找到 urls.txt 文件。")
            return

    if not urls:
        messagebox.showerror("错误", "urls.txt 文件为空，请填写视频链接后重试。")
        return

    # ✅ 逐条采集
    for idx, link in enumerate(urls, 1):
        print(f"▶️ 正在采集 {idx}/{len(urls)}: {link}")
        vid = None
        import re
        m = re.search(r"(?:/video/|modal_id=)(\\d+)", link)
        if m:
            vid = m.group(1)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name = os.path.join(outputs_dir, f"video_{vid or idx}_{ts}.xlsx")
        cmd = f"python3 crawler.py --url '{link}' --out '{out_name}' --profile '{profile}'"
        output = run_cmd(cmd)
        print(output)

    messagebox.showinfo("完成", f"全部采集完成！结果已保存到 outputs 文件夹。")

# ================= GUI 界面 =================
root = tk.Tk()
root.title("Douyin 评论采集助手 (macOS)")
root.geometry("600x320")

tk.Label(root, text="请输入视频链接（留空则读取 urls.txt）:").pack(pady=5)
url_var = tk.StringVar()
tk.Entry(root, textvariable=url_var, width=70).pack(pady=5)

tk.Button(root, text="① 登录抖音", command=login, width=25, height=2).pack(pady=15)
tk.Button(root, text="② 开始采集评论", command=collect, width=25, height=2).pack(pady=10)

tk.Label(root, text="提示：urls.txt 文件需与程序放在同一目录。", fg="gray").pack(pady=15)
root.mainloop()
