#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Slotbound 自动操作脚本（Windows）。

能做的事：
  1. 右下角出现骷髅圆圈（开始按钮）时点击它
  2. 出现决策界面（三个卷轴）时随机点一个
  3. 出现奖励界面（三个卡牌）时点「跳过」

原理：截屏后和几张"参考截图"比颜色，样子对上了就按配置里的坐标点击。
不读取游戏内存、不注入任何东西，纯粹是看屏幕 + 动鼠标。

常用命令：
  python slotbot.py --snap normal      # 截一张参考图
  python slotbot.py --burst 8          # 连拍 8 张
  python slotbot.py --cropfile a.png 100 200 300 200 3   # 放大截图的一块
  python slotbot.py --dry-run --verbose   # 只判定不点击，打印误差
  python slotbot.py                    # 正式运行，F8 停止
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import random
import sys
import time
from ctypes import wintypes

import numpy as np
from PIL import Image, ImageDraw, ImageGrab


def app_dir() -> str:
    """程序所在目录。

    打包成 exe 后 __file__ 指向临时解包目录，配置和截图要跟着 exe 走，
    所以用 sys.executable 定位。
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE = app_dir()
CONFIG_PATH = os.path.join(BASE, "slotbot.json")
LOG_PATH = os.path.join(BASE, "slotbot.log")

GRID_X, GRID_Y = 16, 9
TOL = 18.0
VK_F8 = 0x77
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004

user32 = ctypes.windll.user32
_log_file = None


def log(msg: str) -> None:
    print(msg, flush=True)
    if _log_file is not None:
        _log_file.write(msg + "\n")
        _log_file.flush()


# ------------------------------------------------------------------ 系统

def enable_dpi_awareness() -> None:
    """按物理像素工作，避免 125% / 150% 缩放下点偏。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def minimize_console() -> None:
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        user32.ShowWindow(hwnd, 6)


def click(x, y) -> None:
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def stop_pressed() -> bool:
    return bool(user32.GetAsyncKeyState(VK_F8) & 0x8000)


def grab_image() -> Image.Image:
    try:
        return ImageGrab.grab(all_screens=True)
    except Exception:
        return ImageGrab.grab()


def grab_arr() -> np.ndarray:
    return np.asarray(grab_image().convert("RGB"), dtype=np.float32)


# ------------------------------------------------------------------ 判定

def screen_sig(arr: np.ndarray) -> np.ndarray:
    """整屏压成 16x9 个平均色块。"""
    h, w = arr.shape[:2]
    gy, gx = GRID_Y, GRID_X
    bh, bw = h // gy, w // gx
    return arr[: bh * gy, : bw * gx].reshape(gy, bh, gx, bw, 3).mean(axis=(1, 3))


def spot_sig(arr: np.ndarray, box) -> np.ndarray:
    """一小块区域的平均色。"""
    x, y, bw, bh = box
    return arr[y:y + bh, x:x + bw].reshape(-1, 3).mean(axis=0)


def load_screen_ref(path: str) -> np.ndarray:
    return screen_sig(np.asarray(Image.open(path).convert("RGB"), dtype=np.float32))


def load_spot_ref(path: str, box) -> np.ndarray:
    return spot_sig(np.asarray(Image.open(path).convert("RGB"), dtype=np.float32), box)


# ------------------------------------------------------------------ 工具命令

def cmd_snap(name: str, mark: bool) -> None:
    log("3 秒后截图，请切到游戏画面……")
    time.sleep(3.0)
    img = grab_image()
    if mark:
        d = ImageDraw.Draw(img)
        vx = user32.GetSystemMetrics(76)
        vy = user32.GetSystemMetrics(77)
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        cx, cy = pt.x - vx, pt.y - vy
        d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], outline=(255, 0, 0), width=4)
        d.line([(cx - 55, cy), (cx + 55, cy)], fill=(255, 0, 0), width=3)
        d.line([(cx, cy - 55), (cx, cy + 55)], fill=(255, 0, 0), width=3)
        log(f"   准星画在屏幕坐标 ({pt.x}, {pt.y})")
    path = os.path.join(BASE, f"shot_{name}.png")
    img.save(path)
    log(f"已保存：{path}")


def cmd_burst(count: int, interval: float) -> None:
    log(f"准备连拍 {count} 张，每 {interval} 秒一张。")
    log("现在切到游戏，正常玩一会儿。")
    time.sleep(5.0)
    for i in range(1, count + 1):
        try:
            path = os.path.join(BASE, f"burst_{i:02d}.png")
            grab_image().save(path)
            log(f"  {i}/{count} -> {path}")
        except Exception as e:
            log(f"  {i}/{count} 截图失败：{e}")
        if i < count:
            time.sleep(interval)


def cmd_cropfile(path: str, box, scale: int) -> None:
    x, y, w, h = box
    img = Image.open(path).convert("RGB")
    c = img.crop((x, y, x + w, y + h))
    if scale and scale != 1:
        c = c.resize((c.width * scale, c.height * scale), Image.NEAREST)
    out = os.path.join(BASE, "zoom_" + os.path.splitext(os.path.basename(path))[0] + ".png")
    c.save(out)
    log(f"已保存：{out}  （{c.width}x{c.height}）")


# ------------------------------------------------------------------ 配置

DEFAULT_CONFIG = {
    "poll_interval": 0.3,
    "click_jitter": [0.45, 1.0],
    "park": [960, 620],
    "states": [
        {
            "name": "decision",
            "type": "screen",
            "reference": "shot_decision.png",
            "enabled": True,
            "tol": 18,
            "clicks": [[916, 434], [1223, 446], [1610, 461]],
            "pick": "random",
            "cooldown": 1.5,
        },
        {
            "name": "skip",
            "type": "screen",
            "reference": "shot_skip.png",
            "enabled": True,
            "tol": 18,
            "clicks": [[1269, 928]],
            "pick": "first",
            "cooldown": 1.5,
        },
        {
            "name": "skull",
            "type": "spot",
            "source": "shot_skull.png",
            "box": [1670, 715, 48, 48],
            "enabled": True,
            "tol": 12,
            "clicks": [[1694, 739]],
            "pick": "first",
            "cooldown": 1.0,
            "edge": True,
        },
    ],
}


def ensure_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        log(f"已生成默认配置：{CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_states(cfg):
    out = []
    for st in cfg["states"]:
        if not st.get("enabled", True):
            continue
        try:
            if st.get("type", "screen") == "spot":
                ref = load_spot_ref(os.path.join(BASE, st["source"]), st["box"])
            else:
                ref = load_screen_ref(os.path.join(BASE, st["reference"]))
        except Exception as e:
            log(f"跳过 {st['name']}：读不到参考图（{e}）")
            continue
        out.append((st, ref, float(st.get("tol", TOL))))
    return out


# ------------------------------------------------------------------ 主循环

def run(cfg, dry_run=False, verbose=False, minimize=True):
    states = build_states(cfg)
    if not states:
        log("没有可用的判定项，先按 README 截几张参考图。")
        return

    log("=" * 60)
    log("已加载：" + "、".join(s["name"] for s, _, _ in states))
    log("模式：" + ("dry-run（只判定不点击）" if dry_run else "正式点击"))

    if minimize:
        log("3 秒后自动最小化本窗口，请切到游戏……")
        time.sleep(3.0)
        minimize_console()
        log("（已最小化。玩完按 F8 停止，回来看 slotbot.log）")

    interval = float(cfg.get("poll_interval", 0.3))
    jitter = cfg.get("click_jitter", [0.45, 1.0])
    park = cfg.get("park")
    next_ok = {s["name"]: 0.0 for s, _, _ in states}
    armed = {s["name"]: True for s, _, _ in states}
    last_hit = None
    last_print = 0.0

    try:
        while True:
            if stop_pressed():
                break
            now = time.time()
            live = grab_arr()
            live_sig = screen_sig(live)

            diffs, chosen = {}, None
            for st, ref, tol in states:
                if st.get("type", "screen") == "spot":
                    d = float(np.abs(spot_sig(live, st["box"]) - ref).mean())
                else:
                    d = float(np.abs(live_sig - ref).mean())
                diffs[st["name"]] = d
                if chosen is None and d <= tol:
                    chosen = (st, d)

            if verbose and now - last_print > 1.0:
                log("  " + "  ".join(f"{k}={v:.1f}" for k, v in diffs.items())
                    + (f"   -> {chosen[0]['name']} ✓" if chosen else "   -> 无"))
                last_print = now

            if chosen is None:
                for name in armed:
                    armed[name] = True
                last_hit = None
                time.sleep(interval)
                continue

            st, d = chosen
            name = st["name"]

            if name != last_hit:
                log("  " + "  ".join(f"{k}={v:.1f}" for k, v in diffs.items())
                    + f"   -> {name} ✓")
                last_hit = name

            if now < next_ok.get(name, 0.0):
                time.sleep(interval)
                continue
            if st.get("edge") and not armed[name]:
                time.sleep(interval)
                continue

            clicks = st.get("clicks") or []
            if not clicks:
                time.sleep(interval)
                continue

            cx, cy = random.choice(clicks) if st.get("pick") == "random" else clicks[0]
            log(f"[{name}] 误差={d:.1f} -> {'会点' if dry_run else '点击'} ({cx},{cy})")
            if not dry_run:
                click(cx, cy)
                if park:
                    user32.SetCursorPos(int(park[0]), int(park[1]))
            armed[name] = False
            next_ok[name] = now + float(st.get("cooldown", 1.5))
            time.sleep(random.uniform(*jitter))
    except KeyboardInterrupt:
        pass
    log("已停止。")


def main() -> None:
    global _log_file
    enable_dpi_awareness()

    ap = argparse.ArgumentParser(description="Slotbound 自动操作（看屏幕 + 点鼠标）")
    ap.add_argument("--dry-run", action="store_true", help="只判定不点击")
    ap.add_argument("--verbose", action="store_true", help="每秒打印一次各项误差")
    ap.add_argument("--no-minimize", action="store_true", help="不自动最小化控制台")
    ap.add_argument("--snap", nargs="?", const="screen", metavar="名字",
                    help="截一张参考图，存成 shot_<名字>.png")
    ap.add_argument("--mark", action="store_true", help="配合 --snap：在鼠标位置画准星")
    ap.add_argument("--burst", nargs="?", const=8, type=int, metavar="张数",
                    help="连拍若干张，存成 burst_NN.png")
    ap.add_argument("--interval", type=float, default=1.5, help="连拍间隔秒数")
    ap.add_argument("--cropfile", nargs=6, metavar=("文件", "x", "y", "宽", "高", "倍数"),
                    help="放大已有截图的一块，存成 zoom_<文件名>.png")
    args = ap.parse_args()

    if args.cropfile:
        f, x, y, w, h, s = args.cropfile
        cmd_cropfile(f, (int(x), int(y), int(w), int(h)), int(s))
        return
    if args.burst:
        cmd_burst(args.burst, args.interval)
        return
    if args.snap is not None:
        cmd_snap(args.snap, args.mark)
        return

    _log_file = open(LOG_PATH, "w", encoding="utf-8")
    try:
        run(ensure_config(), dry_run=args.dry_run,
            verbose=args.verbose, minimize=not args.no_minimize)
    finally:
        _log_file.close()


if __name__ == "__main__":
    main()
