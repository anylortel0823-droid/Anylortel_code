# -*- coding: utf-8 -*-
"""
Tkinter 增强版"单人太空射击"小游戏（space_shooter_plus.py）
==========================================================
玩法说明
--------
    左右方向键  : 控制底部飞船左右移动
    空格键      : 发射子弹（有发射冷却，不能无限连射）
    蓝色道具    : 短时间开启"三连发"（一次打出三颗子弹）
    红色道具    : 获得一层护盾，可抵挡一次陨石撞击
    陨石        : 大小不同、速度不同、分值不同；大陨石被打碎会分裂成两个中等陨石，
                  中等陨石再被打碎会分裂成两个小陨石，小陨石被打碎就彻底消失
    飞船受击    : 有护盾先扣护盾，没护盾就扣血；血量归零游戏结束
    难度提升    : 分数越高，陨石生成越快、下落越快（等级实时上升）
    游戏结束    : 弹出窗口询问"是否重新开始"，选"是"重新开局，选"否"关闭窗口退出

技术说明
--------
    只使用 Python 自带标准库 tkinter（含 messagebox），无需 pip 安装任何第三方包。
    Tkinter 没有游戏引擎，动画与"定时逻辑"都靠 root.after(毫秒, 函数) 反复调用实现：
    每 16 毫秒执行一帧（约每秒 60 帧），在每一帧里完成移动、碰撞检测和重绘。

运行方式（请在 PyCharm 中手动运行）：直接运行本文件即可。
"""

import random                        # 标准库：产生随机位置、速度、道具类型
import tkinter as tk                 # 标准库：图形界面
from tkinter import messagebox       # 标准库：游戏结束时弹窗询问是否重开

# ==================== 全局常量（新手可改这些数字调整难度与手感） ====================
WIN_W = 800                 # 画布宽度（像素）
WIN_H = 600                 # 画布高度（像素）
FRAME_MS = 16               # 每帧间隔毫秒数，约等于 60 帧/秒
BG_COLOR = "#0B1021"        # 画布背景色（深空蓝黑，营造太空感）

# ---------- 飞船 ----------
SHIP_W = 44                 # 飞船宽度
SHIP_H = 30                 # 飞船高度
SHIP_SPEED = 8              # 每帧移动像素数（按左右键时的移动速度）
SHIP_COLOR = "#4DD0E1"      # 飞船主体颜色
SHIP_BOTTOM_GAP = 24        # 飞船底部距离窗口底边的距离
START_HP = 3                # 初始血量（陨石撞击会扣血）

# ---------- 子弹 ----------
BULLET_W = 4                # 子弹宽度
BULLET_H = 14               # 子弹高度
BULLET_SPEED = 13           # 子弹每帧向上移动的像素数
BULLET_COLOR = "#FFF176"    # 子弹颜色（亮黄）
SHOOT_COOLDOWN = 11         # 发射冷却帧数：两次发射之间至少要间隔这么多帧
TRIPLE_FRAMES = 480         # 三连发持续帧数（480 帧 ÷ 60 帧/秒 ≈ 8 秒）

# ---------- 陨石 ----------
# 三档陨石参数：半径 / 分值 / 颜色。索引 0=大，1=中，2=小
METEOR_TIERS = [
    {"r": 34, "points": 30, "color": "#8D6E63"},   # 大陨石：最难打，分最高
    {"r": 21, "points": 20, "color": "#A1887F"},   # 中陨石
    {"r": 12, "points": 10, "color": "#BCAAA4"},   # 小陨石：最容易打，分最低
]
METEOR_BASE_SPEED = 1.8     # 1 级时陨石的基础下落速度
METEOR_SPAWN_BASE = 60      # 1 级时陨石的生成间隔（帧）
METEOR_SPAWN_MIN = 12       # 生成间隔的下限（再快也不能比这个更快）
METEOR_SPEED_PER_LEVEL = 0.18   # 每升 1 级，陨石速度增加的系数
METEOR_SPAWN_PER_LEVEL = 3      # 每升 1 级，生成间隔减少的帧数

# ---------- 道具 ----------
ITEM_W = 22                 # 道具宽度
ITEM_H = 22                 # 道具高度
ITEM_SPEED = 3              # 道具下落速度
ITEM_DROP_CHANCE = 0.18     # 陨石被击碎后掉落道具的概率（0~1）
ITEM_TRIPLE_COLOR = "#2196F3"   # 蓝色道具：三连发
ITEM_SHIELD_COLOR = "#F44336"   # 红色道具：护盾

# ---------- 难度 / 等级 ----------
SCORE_PER_LEVEL = 150       # 每累计这么多分升 1 级
MAX_LEVEL = 15              # 等级上限（避免后期完全无法游玩）
HIT_INVINCIBLE_FRAMES = 60  # 被撞后的无敌帧数，防止同一颗陨石连续扣血


class SpaceShooter:
    """游戏主类：把窗口、飞船、子弹、陨石、道具、HUD 的管理都封装在一起。"""

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------
    def __init__(self, root):
        """构造方法：创建窗口与画布，绑定按键，然后开始第一局。"""
        self.root = root                          # 主窗口
        self.root.title("Tkinter 增强版太空射击")   # 窗口标题
        self.root.resizable(False, False)         # 禁止拉伸窗口，保证坐标稳定

        # 画布：所有图形都画在它上面
        self.canvas = tk.Canvas(
            root, width=WIN_W, height=WIN_H,
            bg=BG_COLOR, highlightthickness=0,
        )
        self.canvas.pack()

        # 记录当前按下的方向键：用"集合"记录，可以实现按住不放持续移动
        self.keys = set()
        # 按键按下 / 抬起 / 空格射击
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.bind("<space>", self.on_shoot_key)

        self.hud_score = None   # HUD 文字对象的编号，稍后在 build_hud() 里创建
        self.build_hud()        # 先创建界面文字（分数 / 护盾 / 等级等）
        self.start_new_game()   # 初始化一局的全部数据
        self.loop()             # 进入游戏主循环

    def build_hud(self):
        """创建界面左上/中/右的实时信息文字（HUD = 抬头显示）。"""
        hud_font = ("Microsoft YaHei", 13, "bold")
        # 左上角：分数
        self.hud_score = self.canvas.create_text(
            14, 12, anchor="nw", text="分数：0",
            fill="#FFFFFF", font=hud_font,
        )
        # 正上方居中：等级
        self.hud_level = self.canvas.create_text(
            WIN_W / 2, 12, anchor="n", text="等级：1",
            fill="#FFD54F", font=hud_font,
        )
        # 右上角：护盾层数
        self.hud_shield = self.canvas.create_text(
            WIN_W - 14, 12, anchor="ne", text="护盾：0",
            fill="#FF8A80", font=hud_font,
        )
        # 左上角第二行：血量
        self.hud_hp = self.canvas.create_text(
            14, 36, anchor="nw", text="血量：3",
            fill="#80CBC4", font=hud_font,
        )
        # 左上角第三行：三连发剩余时间提示
        self.hud_buff = self.canvas.create_text(
            14, 60, anchor="nw", text="",
            fill="#64B5F6", font=("Microsoft YaHei", 12),
        )

    # ------------------------------------------------------------------
    # 开始新的一局
    # ------------------------------------------------------------------
    def start_new_game(self):
        """把所有状态重置，并重新创建飞船与 HUD，用于首次开局和"重新开始"。"""
        # 清空画布上的所有图形（包括上一局残留的提示文字）
        self.canvas.delete("all")
        self.build_hud()                # 画布清空后要重新创建 HUD 文字

        self.score = 0                  # 当前分数
        self.level = 1                  # 当前等级（随分数提升）
        self.hp = START_HP              # 剩余血量
        self.shields = 0                # 护盾层数（每层可抵挡一次撞击）
        self.running = True             # 游戏是否进行中
        self.game_over_flag = False     # 是否已经进入结束流程（防止重复弹窗）
        self.invincible = 0             # 无敌剩余帧数
        self.cooldown = 0               # 射击冷却剩余帧数
        self.triple_timer = 0           # 三连发剩余帧数
        self.spawn_timer = 0            # 陨石生成计时器（累加到阈值就生成一颗）
        self.frame = 0                  # 总帧数计数器，用于闪烁等效果

        self.bullets = []               # 我方子弹列表
        self.meteors = []               # 陨石列表
        self.items = []                 # 道具列表

        # 飞船中心坐标（初始在底部正中间）
        self.ship_x = WIN_W / 2
        self.ship_y = WIN_H - SHIP_BOTTOM_GAP - SHIP_H / 2
        self.ship = self.canvas.create_polygon(   # 用多边形画一艘小飞船
            *self.ship_shape(), fill=SHIP_COLOR, outline="#B2EBF2",
        )

        self.refresh_hud()              # 刷新文字显示

    def ship_shape(self):
        """根据飞船中心坐标计算多边形的各个顶点，返回扁平的坐标列表。"""
        x, y = self.ship_x, self.ship_y
        hw, hh = SHIP_W / 2, SHIP_H / 2
        return [
            x, y - hh,                    # 机头（正上方尖角）
            x + hw, y + hh,               # 右下角
            x + hw * 0.45, y + hh * 0.6,  # 右侧内凹
            x - hw * 0.45, y + hh * 0.6,  # 左侧内凹
            x - hw, y + hh,               # 左下角
        ]

    def move_ship_item(self):
        """把画布上的飞船多边形移动到当前坐标。"""
        self.canvas.coords(self.ship, *self.ship_shape())

    # ------------------------------------------------------------------
    # 键盘事件
    # ------------------------------------------------------------------
    def on_key_press(self, event):
        """按下方向键时记录到 keys 集合里，松开前会一直生效。"""
        if event.keysym in ("Left", "Right"):
            self.keys.add(event.keysym)

    def on_key_release(self, event):
        """松开方向键时从集合里移除。"""
        self.keys.discard(event.keysym)

    def on_shoot_key(self, event=None):
        """按下空格：如果冷却结束并且游戏进行中，就发射子弹。"""
        if not self.running or self.cooldown > 0:
            return                      # 冷却中或游戏已结束，直接忽略这次按键
        self.cooldown = SHOOT_COOLDOWN  # 重新进入冷却
        self.fire_bullets()

    # ------------------------------------------------------------------
    # 发射子弹
    # ------------------------------------------------------------------
    def fire_bullets(self):
        """发射子弹：普通状态 1 颗直线向上；三连发状态 3 颗呈扇形散开。"""
        bx = self.ship_x
        by = self.ship_y - SHIP_H / 2          # 从机头位置飞出

        if self.triple_timer > 0:
            # 三连发：左右两颗带一点水平速度，看起来像散弹
            shots = [(-2.2, 0), (0, 0), (2.2, 0)]
        else:
            shots = [(0, 0)]

        for vx, _ in shots:
            item = self.canvas.create_rectangle(
                bx - BULLET_W / 2, by - BULLET_H,
                bx + BULLET_W / 2, by,
                fill=BULLET_COLOR, outline="",
            )
            self.bullets.append({
                "id": item, "x": bx, "y": by,
                "vx": vx, "vy": -BULLET_SPEED,
            })

    # ------------------------------------------------------------------
    # 生成陨石与道具
    # ------------------------------------------------------------------
    def spawn_meteor(self, tier=0, x=None, y=None, vx=None):
        """生成一颗陨石。

        tier=0 大陨石，1 中陨石，2 小陨石；
        x / y / vx 可以由外部指定（大陨石分裂时用，让子陨石从母陨石位置出现）。
        """
        info = METEOR_TIERS[tier]
        r = info["r"]
        if x is None:
            # 从屏幕顶部上方出现，水平位置随机（留出半径，避免贴着边缘）
            x = random.randint(int(r) + 6, int(WIN_W - r) - 6)
            y = -r
            # 下落速度随等级提升；再加一点随机浮动，避免所有陨石整齐划一
            speed = METEOR_BASE_SPEED + (self.level - 1) * METEOR_SPEED_PER_LEVEL
            vy = speed * random.uniform(0.85, 1.25)
            vx = random.uniform(-1.1, 1.1)      # 轻微左右飘移
        else:
            vy = METEOR_BASE_SPEED + (self.level - 1) * METEOR_SPEED_PER_LEVEL
            vy *= random.uniform(0.9, 1.2)

        item = self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill=info["color"], outline="#5D4037", width=2,
        )
        self.meteors.append({
            "id": item, "x": x, "y": y, "r": r,
            "vx": vx, "vy": vy,
            "tier": tier, "points": info["points"],
        })

    def spawn_item(self, x, y):
        """在指定位置生成一个随机道具（蓝色=三连发，红色=护盾）。"""
        if random.random() > ITEM_DROP_CHANCE:
            return                              # 按概率决定这次是否掉落
        kind = random.choice(["triple", "shield"])
        color = ITEM_TRIPLE_COLOR if kind == "triple" else ITEM_SHIELD_COLOR
        item = self.canvas.create_rectangle(
            x - ITEM_W / 2, y - ITEM_H / 2,
            x + ITEM_W / 2, y + ITEM_H / 2,
            fill=color, outline="#FFFFFF", width=2,
        )
        self.items.append({"id": item, "x": x, "y": y, "kind": kind})

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def loop(self):
        """每 16 毫秒执行一帧：先更新逻辑，再预约下一帧。"""
        if self.running:
            self.frame += 1
            self.update_timers()        # 各种倒计时（冷却、三连发、无敌）
            self.update_level()         # 根据分数刷新等级
            self.update_ship()          # 处理左右移动
            self.update_bullets()       # 子弹移动与出界清理
            self.update_meteors()       # 陨石移动与出界清理
            self.update_items()         # 道具移动与出界清理
            self.spawn_logic()          # 按当前等级决定是否生成新陨石
            self.check_collisions()     # 所有碰撞检测
            self.refresh_hud()          # 刷新文字
        self.root.after(FRAME_MS, self.loop)   # 预约下一帧

    def update_timers(self):
        """每帧把各种计时器减 1。"""
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.triple_timer > 0:
            self.triple_timer -= 1
        if self.invincible > 0:
            self.invincible -= 1
            # 无敌期间让飞船闪烁：每隔几帧切换成深色，提示玩家正处于保护状态
            if self.invincible % 8 < 4:
                self.canvas.itemconfig(self.ship, fill="#37474F")
            else:
                self.canvas.itemconfig(self.ship, fill=SHIP_COLOR)
        else:
            self.canvas.itemconfig(self.ship, fill=SHIP_COLOR)

    def update_level(self):
        """按分数计算等级：每 SCORE_PER_LEVEL 分升一级，最高 MAX_LEVEL 级。"""
        new_level = min(MAX_LEVEL, 1 + self.score // SCORE_PER_LEVEL)
        self.level = new_level

    def update_ship(self):
        """根据当前按下的方向键移动飞船，并限制在窗口范围内。"""
        if "Left" in self.keys:
            self.ship_x -= SHIP_SPEED
        if "Right" in self.keys:
            self.ship_x += SHIP_SPEED
        # 左右边界限制，防止飞船飞出窗口
        half = SHIP_W / 2
        self.ship_x = max(half + 4, min(WIN_W - half - 4, self.ship_x))
        self.move_ship_item()

    def update_bullets(self):
        """子弹向上飞行；飞出顶部后从画布和列表中删除。"""
        alive = []
        for b in self.bullets:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if b["y"] + BULLET_H < 0:            # 完全飞出屏幕
                self.canvas.delete(b["id"])
                continue
            self.canvas.coords(
                b["id"],
                b["x"] - BULLET_W / 2, b["y"] - BULLET_H,
                b["x"] + BULLET_W / 2, b["y"],
            )
            alive.append(b)
        self.bullets = alive

    def update_meteors(self):
        """陨石下落（带轻微左右飘移，碰到左右墙会反弹）；落到底部之下就消失。"""
        alive = []
        for m in self.meteors:
            m["x"] += m["vx"]
            m["y"] += m["vy"]
            # 碰到左右边界时水平方向反向，让陨石在屏幕内来回弹
            if m["x"] - m["r"] < 0 or m["x"] + m["r"] > WIN_W:
                m["vx"] = -m["vx"]
                m["x"] = max(m["r"], min(WIN_W - m["r"], m["x"]))
            if m["y"] - m["r"] > WIN_H:          # 掉出底部，直接移除（不扣血）
                self.canvas.delete(m["id"])
                continue
            self.canvas.coords(
                m["id"],
                m["x"] - m["r"], m["y"] - m["r"],
                m["x"] + m["r"], m["y"] + m["r"],
            )
            alive.append(m)
        self.meteors = alive

    def update_items(self):
        """道具缓慢下落，掉出底部就移除。"""
        alive = []
        for it in self.items:
            it["y"] += ITEM_SPEED
            if it["y"] - ITEM_H / 2 > WIN_H:
                self.canvas.delete(it["id"])
                continue
            self.canvas.coords(
                it["id"],
                it["x"] - ITEM_W / 2, it["y"] - ITEM_H / 2,
                it["x"] + ITEM_W / 2, it["y"] + ITEM_H / 2,
            )
            alive.append(it)
        self.items = alive

    def spawn_logic(self):
        """按当前等级决定陨石的生成频率：等级越高，间隔越短。"""
        interval = max(
            METEOR_SPAWN_MIN,
            METEOR_SPAWN_BASE - (self.level - 1) * METEOR_SPAWN_PER_LEVEL,
        )
        self.spawn_timer += 1
        if self.spawn_timer >= interval:
            self.spawn_timer = 0
            # 等级越高，出现大陨石的概率也会略微提高
            weights = [0.35 + self.level * 0.02, 0.35, 0.30]
            tier = random.choices([0, 1, 2], weights=weights, k=1)[0]
            self.spawn_meteor(tier=tier)

    # ------------------------------------------------------------------
    # 碰撞检测
    # ------------------------------------------------------------------
    def check_collisions(self):
        """依次检测：子弹与陨石、飞船与陨石、飞船与道具。"""
        self.check_bullet_meteor()
        self.check_ship_meteor()
        self.check_ship_item()

    def check_bullet_meteor(self):
        """子弹打到陨石：子弹消失、陨石加分并被击碎（大/中陨石会分裂）。"""
        # 用"要删除的对象编号"集合，避免在遍历列表时直接改动列表
        dead_bullets, dead_meteors = set(), set()

        for b in self.bullets:
            if b["id"] in dead_bullets:
                continue
            for m in self.meteors:
                if m["id"] in dead_meteors:
                    continue
                # 判断子弹矩形与陨石外接正方形是否重叠
                if (abs(b["x"] - m["x"]) < m["r"] + BULLET_W / 2
                        and abs(b["y"] - m["y"]) < m["r"] + BULLET_H):
                    dead_bullets.add(b["id"])
                    dead_meteors.add(m["id"])
                    self.destroy_meteor(m)   # 加分 + 分裂 + 可能掉落道具
                    break                    # 一颗子弹只打碎一颗陨石

        # 统一清理：从画布删除、从列表移除
        if dead_bullets:
            self.bullets = [b for b in self.bullets if b["id"] not in dead_bullets]
        if dead_meteors:
            self.meteors = [m for m in self.meteors if m["id"] not in dead_meteors]

    def destroy_meteor(self, meteor):
        """击碎一颗陨石：删图形、加分、按档位分裂、按概率掉落道具。"""
        self.canvas.delete(meteor["id"])
        self.score += meteor["points"]

        tier = meteor["tier"]
        if tier < 2:
            # 大陨石(0) → 两个中陨石(1)；中陨石(1) → 两个小陨石(2)
            for direction in (-1, 1):
                self.spawn_meteor(
                    tier=tier + 1,
                    x=meteor["x"] + direction * 12,
                    y=meteor["y"],
                    vx=direction * random.uniform(1.2, 2.2),
                )
        # 小陨石(2) 被击碎后不再分裂，直接消失

        self.spawn_item(meteor["x"], meteor["y"])   # 有概率掉落道具

    def check_ship_meteor(self):
        """陨石撞到飞船：有护盾先消耗护盾，否则扣血；被撞的陨石一并消失。"""
        if self.invincible > 0 or not self.running:
            return                       # 无敌期间不再重复受伤

        ship_box = self.ship_bbox()      # 飞船的矩形范围
        for m in self.meteors:
            # 陨石中心到飞船矩形的最短距离小于半径，就认为撞上了
            if self.circle_hits_rect(m["x"], m["y"], m["r"], ship_box):
                self.canvas.delete(m["id"])
                self.meteors.remove(m)
                self.take_damage()
                break                    # 一次只处理一次撞击

    def check_ship_item(self):
        """飞船吃到道具：蓝色开三连发，红色加一层护盾。"""
        ship_box = self.ship_bbox()
        for it in list(self.items):
            if self.circle_hits_rect(
                it["x"], it["y"], ITEM_W / 2, ship_box
            ):
                self.canvas.delete(it["id"])
                self.items.remove(it)
                if it["kind"] == "triple":
                    self.triple_timer = TRIPLE_FRAMES     # 重新计时（吃多个可叠加时长）
                else:
                    self.shields += 1                     # 护盾可以叠加多层

    def ship_bbox(self):
        """返回飞船的矩形包围盒 (左, 上, 右, 下)，用于碰撞判断。"""
        return (
            self.ship_x - SHIP_W / 2,
            self.ship_y - SHIP_H / 2,
            self.ship_x + SHIP_W / 2,
            self.ship_y + SHIP_H / 2,
        )

    @staticmethod
    def circle_hits_rect(cx, cy, r, rect):
        """判断圆（陨石/道具）是否与矩形（飞船）相交。

        做法：先求出矩形上离圆心最近的点，再看这个点到圆心的距离是否小于半径。
        """
        left, top, right, bottom = rect
        nearest_x = max(left, min(cx, right))   # 把圆心 x 夹到矩形范围内
        nearest_y = max(top, min(cy, bottom))   # 把圆心 y 夹到矩形范围内
        dx = cx - nearest_x
        dy = cy - nearest_y
        return dx * dx + dy * dy <= r * r

    # ------------------------------------------------------------------
    # 受伤 / 结束 / 刷新界面
    # ------------------------------------------------------------------
    def take_damage(self):
        """受到一次伤害：优先扣护盾，没有护盾才扣血；并给予短暂无敌时间。"""
        if self.shields > 0:
            self.shields -= 1            # 护盾抵挡这一次伤害
        else:
            self.hp -= 1                 # 直接扣血
        self.invincible = HIT_INVINCIBLE_FRAMES   # 进入短暂无敌，防止连续掉血

        if self.hp <= 0:
            self.hp = 0
            self.end_game()

    def end_game(self):
        """游戏结束：停止循环、在画面中央显示结算信息，并延时弹出询问窗口。"""
        if self.game_over_flag:
            return
        self.game_over_flag = True
        self.running = False

        self.canvas.create_text(
            WIN_W / 2, WIN_H / 2 - 30,
            text="游戏结束",
            fill="#FF5252", font=("Microsoft YaHei", 30, "bold"),
        )
        self.canvas.create_text(
            WIN_W / 2, WIN_H / 2 + 20,
            text=f"最终分数：{self.score}    等级：{self.level}",
            fill="#FFFFFF", font=("Microsoft YaHei", 16),
        )
        # 延时 350 毫秒再弹窗，让玩家先看到画面上的结算文字
        self.root.after(350, self.ask_restart)

    def ask_restart(self):
        """弹出询问窗口：选"是"重新开局，选"否"关闭窗口退出游戏。"""
        again = messagebox.askyesno(
            "游戏结束",
            f"最终分数：{self.score}\n达到等级：{self.level}\n\n是否重新开始一局？",
            parent=self.root,
        )
        if again:
            self.start_new_game()        # 重新开局
        else:
            self.root.destroy()          # 关闭窗口，退出程序

    def refresh_hud(self):
        """刷新界面上的实时信息：分数、护盾、等级、血量、三连发状态。"""
        self.canvas.itemconfig(self.hud_score, text=f"分数：{self.score}")
        self.canvas.itemconfig(self.hud_level, text=f"等级：{self.level}")
        self.canvas.itemconfig(self.hud_shield, text=f"护盾：{self.shields}")
        self.canvas.itemconfig(self.hud_hp, text=f"血量：{self.hp}")

        if self.triple_timer > 0:
            # 把帧数换算成秒，保留一位小数，让玩家知道增益还剩多久
            self.canvas.itemconfig(
                self.hud_buff,
                text=f"三连发：{self.triple_timer / 60:.1f} 秒",
            )
        else:
            self.canvas.itemconfig(self.hud_buff, text="")


def main():
    """程序入口：创建主窗口，创建游戏对象，进入事件循环。"""
    root = tk.Tk()             # 创建主窗口
    SpaceShooter(root)         # 创建游戏（内部会自动开始第一局）
    root.mainloop()            # 进入事件循环：等待键盘、鼠标、关闭窗口等操作


# 只有直接运行本文件时才启动游戏；被其他文件 import 时不会自动运行
if __name__ == "__main__":
    main()
