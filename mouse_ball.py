# -*- coding: utf-8 -*-
"""
小球跟随鼠标动画（Tkinter 版）
功能：画布上有一个小球，鼠标移到哪里，小球就平滑地"追"到哪里。
说明：只使用 Python 自带标准库 tkinter，无需安装任何第三方包。
运行：python mouse_ball.py
"""

import tkinter as tk   # Tkinter 是 Python 自带的图形界面库，直接导入即可

# ---------- 全局参数（新手可以随意修改这几个数字看效果） ----------
BALL_RADIUS = 22          # 小球半径（像素），数字越大球越大
BALL_COLOR = "#4A90E2"    # 小球的填充颜色（十六进制颜色码）
CANVAS_W = 800            # 画布宽度（像素）
CANVAS_H = 600            # 画布高度（像素）
EASE = 0.18               # 缓动系数：0~1 之间，越大追得越快，越小越"飘"

# 记录鼠标当前坐标，初始放在画布中心
mouse_x = CANVAS_W / 2
mouse_y = CANVAS_H / 2
# 记录小球当前坐标，初始也放在画布中心
ball_x = CANVAS_W / 2
ball_y = CANVAS_H / 2


def on_mouse_move(event):
    """鼠标移动事件的回调函数：更新目标坐标。

    event.x / event.y 是鼠标在画布内的坐标（相对画布左上角）。
    """
    global mouse_x, mouse_y
    mouse_x = event.x
    mouse_y = event.y


def animate():
    """动画主循环：让小球朝鼠标位置靠近一点点，然后重绘。

    Tkinter 没有内置动画，需要自己用 after() 定时重复调用本函数。
    """
    global ball_x, ball_y

    # 缓动公式：新位置 = 当前位置 + (目标位置 - 当前位置) * 缓动系数
    # 这样小球不会瞬间跳到鼠标上，而是越来越近，形成平滑跟随效果
    ball_x += (mouse_x - ball_x) * EASE
    ball_y += (mouse_y - ball_y) * EASE

    # coords(图形id, 左上角x, 左上角y, 右下角x, 右下角y) 用来移动/改变图形
    # 圆是用外接矩形表示的，所以要减去或加上半径
    canvas.coords(
        ball,
        ball_x - BALL_RADIUS,
        ball_y - BALL_RADIUS,
        ball_x + BALL_RADIUS,
        ball_y + BALL_RADIUS,
    )

    # 每隔 10 毫秒（约等于每秒 100 帧）再执行一次 animate，实现持续动画
    root.after(10, animate)


# ---------- 创建窗口和画布 ----------
root = tk.Tk()                                   # 创建主窗口
root.title("Tkinter 小球跟随鼠标动画")             # 设置窗口标题
root.resizable(False, False)                     # 禁止拖动改变窗口大小，避免画布错位

canvas = tk.Canvas(
    root,
    width=CANVAS_W,
    height=CANVAS_H,
    bg="#F5F7FA",        # 画布背景色（浅灰蓝）
    highlightthickness=0,  # 去掉画布默认的边框线
)
canvas.pack()            # 把画布放进窗口并自动布局

# 在画布上创建小球（create_oval 的参数是外接矩形的左上角和右下角）
ball = canvas.create_oval(
    ball_x - BALL_RADIUS,
    ball_y - BALL_RADIUS,
    ball_x + BALL_RADIUS,
    ball_y + BALL_RADIUS,
    fill=BALL_COLOR,     # 填充颜色
    outline="",          # 不画描边
)

# 在画布上写一行提示文字
canvas.create_text(
    12,
    12,
    anchor="nw",                              # 以文字左上角对齐到 (12, 12)
    text="把鼠标移到画布上，小球会跟着你跑～",
    fill="#888888",
    font=("Microsoft YaHei", 12),
)

# 绑定鼠标移动事件：鼠标在画布上移动时自动调用 on_mouse_move
canvas.bind("<Motion>", on_mouse_move)

# 启动动画循环
animate()

# 进入 Tkinter 事件循环（程序会停在这里，等待用户的鼠标、键盘等操作）
root.mainloop()
