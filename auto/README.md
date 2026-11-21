# Slotbound Auto

给单机游戏《转运军团》(Slotbound) 用的自动闯关脚本（Windows）。看屏幕、动鼠标，不读游戏内存，也不往游戏里注入任何东西。

它做三件事：

| 情况 | 动作 |
| --- | --- |
| 右下角出现骷髅圆圈（开始按钮） | 点它 |
| 出现决策界面（三个卷轴） | 随机点一个 |
| 出现奖励界面（三个卡牌） | 点「跳过」 |

## 仓库内容

| 文件 | 说明 |
| --- | --- |
| `slotbot.py` | 脚本本体 |
| `run.bat` | 双击启动 |
| `build.bat` | 打包成 exe（可选） |
| `shot_decision.png` | 决策界面（三个卷轴）的参考截图 |
| `shot_skip.png` | 奖励界面（三个卡牌）的参考截图 |
| `shot_skull.png` | 骷髅圆圈出现时的参考截图 |
| `GUIDE.md` | 原理、坐标怎么量、怎么加新界面、阈值怎么调 |
| `slotbot.json` | 配置，**首次运行自动生成**（已 gitignore） |

三张参考图都是 1920×1080 全屏截的。**如果你的分辨率不是 1920×1080，或者 UI 缩放不同，需要自己重截**。

## 环境

- Windows 10 / 11
- Python 3.9+
- `pip install -r requirements.txt`

## 双击启动

**直接双击 `run.bat`** 就行。它会自动：

1. 找 Python（`python` 或 `py`）
2. 第一次运行时自动安装依赖
3. 启动脚本，3 秒后把自己最小化

想放桌面的话：右键 `run.bat` → 发送到 → 桌面快捷方式。

## 快速开始

**1. 截参考图**

仓库里已经带了三张（1920×1080）。分辨率不一样的话，自己重截：

```bat
python slotbot.py --snap decision     :: 停在决策界面时
python slotbot.py --snap skip         :: 停在奖励界面时
python slotbot.py --snap skull        :: 骷髅圆圈出现时
python slotbot.py --snap normal       :: 普通战斗界面（当"都不是"的参照）
```

每条命令都会等 3 秒再截，所以回车后要立刻切回游戏。

**2. 量坐标**

需要知道该点哪的话，把截图放大看：

```bat
python slotbot.py --cropfile shot_skip.png 1100 880 400 160 3
```

会存成 `zoom_shot_skip.png`，放大 3 倍。（`x y 宽 高 倍数`）

**3. 试运行**

```bat
python slotbot.py --dry-run --verbose
```

每秒钟打印一行误差：

```
  decision=64.8  skip=62.1  skull=3.2   -> skull ✓
```

数字越小越像。同一界面一般 0~12，不同界面 40 以上。阈值在 `slotbot.json` 里按状态配（默认 `screen` 18、`spot` 12）。

**4. 正式运行**

```bat
python slotbot.py
```

按 **F8** 随时停止。运行结果写在 `slotbot.log`。

## 打包成 exe

不想装 Python 的话可以打包成单个 exe：

```bat
build.bat
```

产出 `dist\slotbot.exe`。把它和 `slotbot.json`、三张 `shot_*.png` 放在同一个文件夹里就能直接双击运行。

两点注意：

- **不要加 `--noconsole`**。程序靠控制台打印和自动最小化工作，去掉控制台窗口会直接报错。
- PyInstaller 打的包**杀毒软件可能误报**（没有签名，又带自解压行为），介意的话自己加白名单。

## 配置

首次运行会生成 `slotbot.json`：

```json
{
  "poll_interval": 0.3,
  "click_jitter": [0.45, 1.0],
  "park": [960, 620],
  "states": [
    {
      "name": "decision",
      "type": "screen",
      "reference": "shot_decision.png",
      "tol": 18,
      "clicks": [[916, 434], [1223, 446], [1610, 461]],
      "pick": "random",
      "cooldown": 1.5
    }
  ]
}
```

| 字段 | 说明 |
| --- | --- |
| `type` | `screen` 整屏判定；`spot` 局部判定 |
| `reference` / `source` | 参考截图文件名 |
| `box` | 仅 `spot`：`[x, y, 宽, 高]`，要比对的区域 |
| `tol` | 判定阈值，越小越严格 |
| `clicks` | 命中后要点的坐标列表 |
| `pick` | `random` 随机选一个 / `first` 固定点第一个 |
| `edge` | `true` 时点一次就锁定，等界面消失再出现才允许再点（防止连点） |
| `cooldown` | 两次点击之间的最短间隔（秒） |
| `park` | 点完之后把鼠标挪到这里，免得挡住判定区域 |

`states` 的**顺序就是优先级**，先匹配上的先执行。

## 常见问题

**点了但没点中**
截图是在 125% / 150% 缩放下截的，而程序按物理像素算。脚本启动时已调用 `SetProcessDpiAwareness`，若仍偏移，把游戏改成窗口全屏再量一次坐标。

**某个界面认不出来**
用 `--dry-run --verbose` 看那个界面的误差值。如果接近但没低于阈值，把该状态的 `tol` 调大 2~4。

**乱点**
反过来，把 `tol` 调小 2~3，或者把 `clicks` 改到更靠边、更安全的位置。

**骷髅圆圈点了不止一次**
检查 `edge` 是否为 `true`。它为 `true` 时，点完会锁定，直到该区域的样子变化（按钮消失）才重新可用。

## 说明

- 只针对单机游戏，不涉及联机、反作弊或任何绕过机制。
- 仓库里**不包含**游戏本体，只有脚本和三张界面参考截图。
- 请支持正版。

## 贡献者

- [program84](https://github.com/program84) — 需求、实机测试、界面坐标标定
- [deepseek](https://github.com/deepseek) — 脚本实现与文档

## License

MIT
