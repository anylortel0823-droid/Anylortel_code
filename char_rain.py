# -*- coding: utf-8 -*-
"""
终端字符雨动画（Tkinter 无关，纯终端版）
功能：在命令行窗口里让一排排字符不断往下"落"，形成类似黑客帝国数字雨的动画。
说明：只使用 Python 自带标准库（os / sys / time / random / shutil），无需安装任何第三方包。
运行：python char_rain.py
退出：按 Ctrl + C 即可停止。
注意：Windows 10 及以上自带的终端（cmd / PowerShell / Windows Terminal）已支持本脚本用到的
      ANSI 转义控制码；若某些老终端显示乱码，属于终端限制，不是代码问题。
"""

import os       # 用于清屏、读取终端宽度等系统相关操作
import random   # 用于生成随机字符、随机起始位置、随机速度
import shutil   # 用于获取终端窗口大小（列数、行数）
import sys      # 用于把内容立刻输出、以及处理退出
import time     # 用于控制动画帧间隔（每秒刷新多少次）

# ---------- 可调参数（新手可随意修改这几个数字观察效果） ----------
FPS = 20                  # 每秒刷新帧数，数字越大幅度越快
TRAIL_LEN = 8             # 每条"雨线"的拖尾长度（尾巴上的字符个数）
DENSITY = 0.22            # 每一列出现雨线的概率，越大雨越密（0~1）
CHARS = "01" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "あいうえおカキクケコ"  # 可下落的所有字符

# 深绿到浅绿的 ANSI 颜色码，越靠前越亮（用于画拖尾的渐变色）
GREEN_SHADES = [82, 46, 40, 34, 28, 22]   # 256 色模式下的绿色号
DIM = 240                                 # 背景/旧字符使用的暗灰色号

# ---------- ANSI 转义码常量（控制终端光标与颜色） ----------
ESC = "\033["
CLEAR = ESC + "2J"       # 清空整个屏幕
HOME = ESC + "H"         # 光标移动到左上角 (第1行第1列)
HIDE_CURSOR = ESC + "?25l"   # 隐藏光标，避免光标闪烁影响观感
SHOW_CURSOR = ESC + "?25h"   # 恢复显示光标


def term_size():
    """获取当前终端大小，返回 (列数, 行数)。

    优先用 shutil.get_terminal_size()；如果拿到的是默认兜底值，就再尝试
    用 os.get_terminal_size() 读一次，保证在真实终端里拿到正确尺寸。
    """
    size = shutil.get_terminal_size(fallback=(80, 24))
    cols, rows = size.columns, size.lines
    try:
        real = os.get_terminal_size()
        cols, rows = real.columns, real.lines
    except OSError:
        pass  # 非真实终端（比如被重定向到文件）时会报错，忽略即可
    return max(cols, 20), max(rows, 10)


def setup_console():
    """Windows 终端兼容处理：开启 ANSI 转义支持（其他系统会自动跳过）。"""
    if os.name == "nt":
        os.system("")  # 这一句会让部分 Windows 控制台启用 VT 转义解析
    try:
        # 尽量把标准输出切成 UTF-8，避免中文或日文假名显示成乱码
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # 老版本 Python 没有 reconfigure，忽略即可


def build_drops(cols):
    """初始化每一列雨线的状态，返回一个列表，每个元素描述一列的当前情况。

    每个元素是一个字典：
        head   当前"雨滴头部"所在行号（不断增大表示往下落）
        speed  每次刷新下落几行（越大越快）
        length 这条雨线的拖尾长度
        alive  这一列当前是否正在下雨
    """
    drops = []
    for _ in range(cols):
        drops.append({
            "head": random.randint(-20, 0),   # 起始位置在屏幕上方，让雨"从天上落下"
            "speed": random.choice([1, 1, 1, 2, 2, 3]),
            "length": random.randint(4, TRAIL_LEN),
            "alive": random.random() < DENSITY,  # 按概率决定这一列要不要下雨
        })
    return drops


def render(drops, rows):
    """把当前所有雨线画到屏幕上。

    关键技巧：用 ANSI 码把光标移动到指定行，再输出单个字符，
    这样每一帧只重写需要变的地方，比整屏清空重画要流畅得多。
    """
    buf = [HOME]  # 每次绘制都先把光标挪回左上角
    for col, drop in enumerate(drops):
        if not drop["alive"]:
            continue  # 这一列没有雨，跳过
        head = drop["head"]
        # tail 从头部往上逐格画拖尾：越靠上的字符颜色越暗，形成尾部渐隐效果
        for offset in range(drop["length"] + 1):
            row = head - offset
            if row < 0 or row >= rows:
                continue  # 超出屏幕范围的行不用画
            if offset == 0:
                color = GREEN_SHADES[0]          # 头部最亮
                ch = random.choice(CHARS)        # 头部字符每帧随机变化，看起来在闪烁
            else:
                idx = min(offset, len(GREEN_SHADES) - 1)
                color = GREEN_SHADES[idx]
                ch = random.choice(CHARS)
            # 语法：ESC[行;列H 移动光标，ESC[38;5;色号m 设置前景色，ESC[0m 复位
            buf.append(f"{ESC}{row + 1};{col + 1}H{ESC}38;5;{color}m{ch}")
    buf.append(ESC + "0m")  # 画完复位颜色，防止影响后续输出
    sys.stdout.write("".join(buf))
    sys.stdout.flush()      # 立刻送到终端，否则会攒在缓冲区里看不到动画


def main():
    """主函数：初始化终端，然后进入无限循环不断刷新画面。"""
    setup_console()
    sys.stdout.write(CLEAR + HIDE_CURSOR)  # 清屏并隐藏光标
    sys.stdout.flush()

    try:
        while True:
            cols, rows = term_size()
            # 终端尺寸会随窗口缩放变化，所以每帧都检查一次
            if "drops" not in dir() or len(drops) != cols:
                drops = build_drops(cols)

            # 逐列推进雨滴
            for drop in drops:
                if not drop["alive"]:
                    # 已经停下雨的列，有小概率重新开始下雨，让画面持续变化
                    if random.random() < 0.02:
                        drop.update({
                            "alive": True,
                            "head": random.randint(-10, 0),
                            "speed": random.choice([1, 1, 1, 2, 2, 3]),
                            "length": random.randint(4, TRAIL_LEN),
                        })
                    continue
                drop["head"] += drop["speed"]          # 头部往下移动
                # 头部完全离开屏幕底部后，这一列本轮结束
                if drop["head"] - drop["length"] > rows:
                    drop["alive"] = False

            render(drops, rows)
            time.sleep(1.0 / FPS)  # 控制刷新速度，形成稳定动画节奏
    except KeyboardInterrupt:
        # 用户按下 Ctrl + C 时优雅退出
        pass
    finally:
        # 无论怎么退出，都要恢复光标并复位颜色，否则终端会变"脏"
        sys.stdout.write(ESC + "0m" + SHOW_CURSOR + "\n")
        sys.stdout.flush()
        print("字符雨已停止，感谢观看 ~")


# 直接运行本文件时才启动动画；被其他文件 import 时不会自动播放
if __name__ == "__main__":
    main()
