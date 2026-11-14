# -*- coding: utf-8 -*-
"""
Tkinter 图形打砖块小游戏（brick_break.py）
=========================================
玩法说明：
    1. 鼠标在窗口内左右移动，底部的挡板会跟着鼠标走；
    2. 小球碰到左右墙壁、顶部会反弹，碰到挡板也会反弹；
    3. 小球撞碎彩色砖块，砖块消失并加分（越靠上的砖块分值越高）；
    4. 小球掉到窗口底部（没接住）→ 游戏结束；
    5. 所有砖块被打碎 → 显示通关；
    6. 游戏结束后按键盘 R 键可以重新开始；
    7. 直接点窗口右上角的关闭按钮即可退出游戏。

技术说明：
    只使用 Python 自带标准库 tkinter（Python 安装时自带，无需 pip 安装任何第三方包）。
    Tkinter 没有内置游戏引擎，动画靠 root.after(毫秒, 函数) 定时反复调用实现。

运行方式：python brick_break.py
"""

import tkinter as tk   # Python 自带的图形界面库（标准库，无需安装）

# ==================== 全局常量（新手可直接改这些数字调整游戏手感） ====================
WIN_W = 800            # 窗口/画布宽度（像素）
WIN_H = 600            # 窗口/画布高度（像素）
FPS_DELAY = 16         # 每一帧间隔毫秒数，16 毫秒约等于每秒 60 帧，数值越小球越快

PADDLE_W = 120         # 挡板宽度
PADDLE_H = 14          # 挡板高度
PADDLE_Y = WIN_H - 40  # 挡板顶部距窗口顶部的距离（即挡板贴在底部）
PADDLE_COLOR = "#2C3E50"

BALL_R = 9             # 小球半径
BALL_COLOR = "#F39C12"
BALL_SPEED = 10         # 小球每一帧移动的像素数（总速度）
BALL_MAX_DX = 4.5      # 撞击挡板后水平速度的最大值（防止球飞得太"平"）

BRICK_ROWS = 6         # 砖块行数
BRICK_COLS = 10        # 砖块列数
BRICK_W = 70           # 单块砖宽度
BRICK_H = 24           # 单块砖高度
BRICK_GAP = 4          # 砖块之间的缝隙
BRICK_TOP = 60         # 第一行砖块的顶部 y 坐标（给顶部得分文字留出空间）
# 每一行砖块的颜色（从上到下），使用十六进制颜色码
BRICK_COLORS = ["#E74C3C", "#E67E22", "#F1C40F", "#2ECC71", "#1ABC9C", "#3498DB"]

# 计算砖块区域水平居中所需的左边距
BRICKS_TOTAL_W = BRICK_COLS * BRICK_W + (BRICK_COLS - 1) * BRICK_GAP
BRICK_LEFT = (WIN_W - BRICKS_TOTAL_W) // 2


class BrickBreakGame:
    """打砖块游戏主类：把窗口、挡板、小球、砖块的创建与更新都封装在一起。"""

    def __init__(self, root):
        """构造方法：程序一运行就会执行，用来搭建窗口和游戏元素。"""
        self.root = root                      # 保存主窗口对象，方便后面使用
        self.root.title("Tkinter 打砖块小游戏")  # 设置窗口标题
        self.root.resizable(False, False)     # 禁止拉伸窗口，避免画布布局错乱

        # 创建画布：所有图形（挡板、小球、砖块、文字）都画在上面
        self.canvas = tk.Canvas(
            root,
            width=WIN_W,
            height=WIN_H,
            bg="#ECF0F1",            # 画布背景色（浅灰）
            highlightthickness=0,    # 去掉画布默认的细边框
        )
        self.canvas.pack()

        # 绑定事件：鼠标移动 → 控制挡板；键盘 R → 重新开始
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<r>", self.restart)
        self.root.bind("<R>", self.restart)

        # 游戏状态变量
        self.score = 0            # 当前得分
        self.running = True       # 游戏是否进行中（False 表示已经结束/通关）
        self.game_over = False    # 是否失败结束
        self.win = False          # 是否通关

        # 先创建固定的界面元素（得分文字、挡板），再开始新一局
        self.score_text = self.canvas.create_text(
            16, 16, anchor="nw", text="得分：0",
            fill="#2C3E50", font=("Microsoft YaHei", 14, "bold"),
        )
        self.paddle = self.canvas.create_rectangle(
            0, 0, 0, 0, fill=PADDLE_COLOR, outline=""
        )
        self.paddle_x = WIN_W / 2   # 挡板中心点的 x 坐标，初始在正中间

        self.start_new_game()       # 初始化小球和砖块
        self.loop()                 # 启动游戏主循环（动画）

    # ------------------------------------------------------------------
    # 初始化 / 重新开始
    # ------------------------------------------------------------------
    def start_new_game(self):
        """重置一局的全部数据：分数归零、重建小球与砖块、清掉结束提示。"""
        # 删除上一局残留的提示文字（如果有）
        if getattr(self, "msg_text", None) is not None:
            self.canvas.delete(self.msg_text)
            self.msg_text = None

        self.score = 0
        self.running = True
        self.game_over = False
        self.win = False
        self.canvas.itemconfig(self.score_text, text="得分：0")

        self.draw_paddle()    # 把挡板画到当前位置
        self.create_ball()    # 创建小球
        self.create_bricks()  # 创建所有砖块

    def draw_paddle(self):
        """根据挡板中心坐标，更新挡板矩形的四个顶点坐标。"""
        half = PADDLE_W / 2
        self.canvas.coords(
            self.paddle,
            self.paddle_x - half, PADDLE_Y,
            self.paddle_x + half, PADDLE_Y + PADDLE_H,
        )

    def create_ball(self):
        """创建小球（用圆形表示）并让它停在挡板正上方，同时给出初始运动方向。"""
        self.ball_x = self.paddle_x          # 小球初始 x 与挡板中心对齐
        self.ball_y = PADDLE_Y - BALL_R - 1  # 小球紧贴在挡板上方

        self.ball = self.canvas.create_oval(
            self.ball_x - BALL_R, self.ball_y - BALL_R,
            self.ball_x + BALL_R, self.ball_y + BALL_R,
            fill=BALL_COLOR, outline="",
        )

        # 初始速度：斜向右上方飞出去（dy 为负数表示向上）
        self.dx = BALL_SPEED * 0.6
        self.dy = -BALL_SPEED * 0.8

    def create_bricks(self):
        """按行、列循环生成所有砖块，并记录每一块的信息便于碰撞检测。"""
        self.bricks = []  # 存放所有砖块的信息字典
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = BRICK_LEFT + col * (BRICK_W + BRICK_GAP)   # 左上角 x
                y = BRICK_TOP + row * (BRICK_H + BRICK_GAP)    # 左上角 y
                item = self.canvas.create_rectangle(
                    x, y, x + BRICK_W, y + BRICK_H,
                    fill=BRICK_COLORS[row % len(BRICK_COLORS)],
                    outline="#FFFFFF",   # 白色描边让砖块之间有分隔感
                    width=2,
                )
                self.bricks.append({
                    "id": item,                 # 画布图形编号，用于删除
                    "x": x, "y": y,             # 左上角坐标
                    "w": BRICK_W, "h": BRICK_H, # 宽高
                    # 越上面的砖块分值越高：第 0 行 60 分，往下递减 10 分
                    "points": (BRICK_ROWS - row) * 10,
                    "alive": True,              # 是否还存在
                })

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------
    def on_mouse_move(self, event):
        """鼠标在画布上移动时触发：把挡板中心移到鼠标位置（并限制在窗口内）。"""
        half = PADDLE_W / 2
        # max/min 用来做边界限制，保证挡板不会跑出窗口左右两侧
        self.paddle_x = max(half, min(WIN_W - half, event.x))
        self.draw_paddle()

    def restart(self, event=None):
        """按下 R 键时触发：无论当前是失败还是通关，都重新开一局。"""
        self.start_new_game()

    # ------------------------------------------------------------------
    # 游戏主循环
    # ------------------------------------------------------------------
    def loop(self):
        """每一帧要做的事情：移动小球 → 处理各种碰撞 → 重绘 → 预约下一帧。"""
        if self.running:
            self.move_ball()
            self.check_collisions()
        # after(毫秒, 函数)：让 Tkinter 在指定毫秒后自动再调用一次本函数，
        # 这样一帧接一帧就形成了动画。
        self.root.after(FPS_DELAY, self.loop)

    def move_ball(self):
        """根据速度向量移动小球，并更新画布上圆形的位置。"""
        self.ball_x += self.dx
        self.ball_y += self.dy
        self.canvas.coords(
            self.ball,
            self.ball_x - BALL_R, self.ball_y - BALL_R,
            self.ball_x + BALL_R, self.ball_y + BALL_R,
        )

    def check_collisions(self):
        """依次检测：墙壁、挡板、砖块、是否掉出底部。"""
        # ---------- 1. 左右墙壁 ----------
        if self.ball_x - BALL_R <= 0:            # 碰到左墙
            self.ball_x = BALL_R                 # 把球推回墙内，避免卡住
            self.dx = abs(self.dx)               # 水平速度取正 → 向右飞
        elif self.ball_x + BALL_R >= WIN_W:      # 碰到右墙
            self.ball_x = WIN_W - BALL_R
            self.dx = -abs(self.dx)              # 水平速度取负 → 向左飞

        # ---------- 2. 顶部墙壁 ----------
        if self.ball_y - BALL_R <= 0:
            self.ball_y = BALL_R
            self.dy = abs(self.dy)               # 垂直速度取正 → 向下飞

        # ---------- 3. 底部：没接住，游戏结束 ----------
        if self.ball_y - BALL_R > WIN_H:
            self.end_game(win=False)
            return

        # ---------- 4. 与挡板碰撞 ----------
        paddle_top = PADDLE_Y
        paddle_left = self.paddle_x - PADDLE_W / 2
        paddle_right = self.paddle_x + PADDLE_W / 2
        # 只有球在向下运动、且球的位置落在挡板范围内时才判定为击中挡板
        if (self.dy > 0
                and self.ball_y + BALL_R >= paddle_top
                and self.ball_y - BALL_R <= paddle_top + PADDLE_H
                and paddle_left - BALL_R <= self.ball_x <= paddle_right + BALL_R):
            self.ball_y = paddle_top - BALL_R    # 把球放到挡板上方，防止穿模
            self.dy = -abs(self.dy)              # 垂直方向反弹（向上）
            # 击中位置离挡板中心越远，水平速度越大，这样玩家能"瞄准"方向
            offset = (self.ball_x - self.paddle_x) / (PADDLE_W / 2)
            self.dx = offset * BALL_MAX_DX
            # 保证球始终有向上的速度，避免出现水平"贴边"来回飞的死局
            if abs(self.dy) < 2:
                self.dy = -2

        # ---------- 5. 与砖块碰撞 ----------
        for brick in self.bricks:
            if not brick["alive"]:
                continue                       # 已经碎掉的砖块不用检测
            if self.hit_brick(brick):
                self.break_brick(brick)
                break                          # 一帧只处理一块，避免速度被反复取反

        # ---------- 6. 判断是否全部打碎（通关） ----------
        if all(not b["alive"] for b in self.bricks):
            self.end_game(win=True)

    def hit_brick(self, brick):
        """判断小球（圆形按外接正方形处理）与某块砖块是否重叠。

        做法：分别计算两个矩形在 x、y 方向上的重叠长度，两个都大于 0 就是撞上了。
        """
        bx1, by1 = brick["x"], brick["y"]
        bx2, by2 = bx1 + brick["w"], by1 + brick["h"]
        ball_l, ball_t = self.ball_x - BALL_R, self.ball_y - BALL_R
        ball_r, ball_b = self.ball_x + BALL_R, self.ball_y + BALL_R

        overlap_x = min(ball_r, bx2) - max(ball_l, bx1)   # x 方向重叠宽度
        overlap_y = min(ball_b, by2) - max(ball_t, by1)   # y 方向重叠高度
        if overlap_x <= 0 or overlap_y <= 0:
            return False   # 有一个方向没重叠，说明没碰到

        # 重叠较小的那个方向，就是球撞过来的方向，只需要让该方向的速度反向
        if overlap_x < overlap_y:
            self.dx = -self.dx          # 从左右撞上，水平反弹
        else:
            self.dy = -self.dy          # 从上下撞上，垂直反弹
        return True

    def break_brick(self, brick):
        """打碎砖块：从画布上删除它、标记为不存在，并加分。"""
        brick["alive"] = False
        self.canvas.delete(brick["id"])          # 删除画布上的矩形
        self.score += brick["points"]            # 加分
        self.canvas.itemconfig(                      # 刷新得分文字
            self.score_text, text=f"得分：{self.score}"
        )

    # ------------------------------------------------------------------
    # 结束与结算
    # ------------------------------------------------------------------
    def end_game(self, win):
        """结束这一局，并在屏幕中央显示结算文字。"""
        if not self.running:
            return                    # 防止同一次结束被重复触发
        self.running = False
        self.win = win
        self.game_over = not win

        if win:
            title = "🎉 恭喜通关！"
            color = "#27AE60"         # 通关用绿色
        else:
            title = "游戏结束"
            color = "#C0392B"         # 失败用红色

        # 在画布正中央显示两行文字（标题 + 提示）
        self.msg_text = self.canvas.create_text(
            WIN_W / 2, WIN_H / 2 - 20,
            text=f"{title}\n\n最终得分：{self.score}\n\n按 R 键重新开始",
            fill=color,
            font=("Microsoft YaHei", 24, "bold"),
            justify="center",         # 多行文字居中对齐
        )


def main():
    """程序入口：创建主窗口并进入 Tkinter 事件循环。"""
    root = tk.Tk()                 # 创建主窗口
    BrickBreakGame(root)           # 创建游戏对象，游戏立即开始
    root.mainloop()                # 进入事件循环，等待鼠标/键盘/关闭窗口等操作
    # 点击窗口右上角关闭按钮时，mainloop() 返回，程序随即结束，即"关闭窗口退出游戏"


# 只有直接运行本文件时才启动游戏；被其他文件 import 时不会自动运行
if __name__ == "__main__":
    main()
