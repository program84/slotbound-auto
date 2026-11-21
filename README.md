# 《转运军团》(Slotbound) 自动闯关脚本

看屏幕、动鼠标的自动操作脚本，不读游戏内存，也不注入任何东西。

代码和文档都在 [`auto/`](auto/) 目录下：

```
auto/
├─ run.bat          双击启动
├─ slotbot.py       脚本本体
├─ build.bat        打包成 exe（可选）
├─ requirements.txt
├─ shot_decision.png  三张参考截图
├─ shot_skip.png
├─ shot_skull.png
├─ README.md        完整说明
├─ GUIDE.md         原理与调参
├─ LICENSE          MIT
└─ .gitignore
```

## 快速开始

1. 装 Python 3.10+
2. 把 `auto/` 整个文件夹拷到任意位置
3. 双击 `auto/run.bat`（第一次会自动装依赖）
4. 按 F8 停止

详细说明见 [auto/README.md](auto/README.md)，原理和调参见 [auto/GUIDE.md](auto/GUIDE.md)。

## 它做什么

| 情况 | 动作 |
| --- | --- |
| 右下角出现骷髅圆圈（开始按钮） | 点它 |
| 出现决策界面（三个卷轴） | 随机点一个 |
| 出现奖励界面（三个卡牌） | 点「跳过」 |

## 说明

- 只针对单机游戏，不涉及联机、反作弊或任何绕过机制。
- 仓库里**不包含**游戏本体，只有脚本和三张界面参考截图。
- 请支持正版。

## License

MIT
