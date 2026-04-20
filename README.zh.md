# hermes-computer-use

[English](README.md) · [日本語](README.ja.md) · **中文** · [한국어](README.ko.md)

[![CI](https://github.com/Noah3521/hermes-computer-use/actions/workflows/ci.yml/badge.svg)](https://github.com/Noah3521/hermes-computer-use/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hermes-computer-use.svg)](https://pypi.org/project/hermes-computer-use/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: WSL2 Ubuntu](https://img.shields.io/badge/platform-WSL2%20Ubuntu-0078D6?logo=ubuntu&logoColor=white)](docs/WSL_SETUP.md)

> **支持环境:仅 Windows 11 + WSL2 Ubuntu 22.04 / 24.04。** 完整说明见 [docs/WSL_SETUP.md](docs/WSL_SETUP.md)。

**像素级浏览器自动化 MCP 服务器。** 给任何 MCP 客户端(hermes-agent、Claude Code、Codex 等)提供 21 个工具,用于驱动跑在 Xvfb 虚拟显示器上的真实 Chrome 浏览器。输入是截图(用于视觉推理),输出是操作系统层的鼠标 / 键盘事件。**无 CDP,无 `navigator.webdriver`,无 DOM 捷径。**

<p align="center"><img src="docs/assets/demo-snp500.gif" width="760" alt="代理打开 Chrome、在 Google 搜索框中输入「snp500」按回车,Google 返回包含 S&P 500 指数实时行情卡的正常结果页。全程由像素截图 + xdotool 驱动。"></p>

> **GIF 内容** — 代理启动 Chrome、聚焦 Google 搜索框、输入 `snp500` 并回车,Google 返回包含 S&P 500 实时报价卡的完整 SERP。同样的流程在 Playwright 下通常会触发「异常流量」或 CAPTCHA;本项目不会被识别,因为浏览器本身就是原生 Chrome,输入也是原生 X11,没有自动化指纹。

## 为什么做这个

| | Playwright / CDP | hermes-computer-use |
|---|---|---|
| `navigator.webdriver` | `true`(可检测) | `undefined` |
| CDP 端点 | 开放 | 无 |
| DOM 访问 | 直接(快,但对 UI 重写脆弱) | 仅截图(慢,但对 UI 改版更鲁棒) |
| Anti-bot 足迹 | 大,需要不断打补丁 | 近乎为零:原生 Chrome + 原生 X 输入 |
| 适用场景 | 自有站点的稳定流程 | 代理像人类一样操作陌生站点 |

遇到 Cloudflare、Kasada、reCAPTCHA、DataDome 保护的站点,Playwright 常被拦,本栈通常能通过。

## 安装

前置:Windows 11、WSL2 + Ubuntu 22.04/24.04、已启用 systemd。完整指南见 [docs/WSL_SETUP.md](docs/WSL_SETUP.md)。

以下所有命令都在 **WSL shell 内** 执行。

```bash
# 从 PyPI
pip install "hermes-computer-use[novnc]"

# 或从源代码
git clone https://github.com/Noah3521/hermes-computer-use.git ~/hermes-computer-use
cd ~/hermes-computer-use
bash scripts/setup.sh                       # 系统包 + Chrome (sudo)
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[novnc]"
mkdir -p ~/.config/systemd/user
cp systemd/*.example ~/.config/systemd/user/
sudo loginctl enable-linger "$USER"
systemctl --user daemon-reload
systemctl --user enable --now computer-use.service
```

冒烟测试:`python examples/smoke_test.py`

## 工具一览(21 个)

| 分类 | 工具 |
|---|---|
| 状态 | `screen_info`, `cursor_position` |
| 截图 | `screenshot` |
| 指针 | `move`, `left_click`, `right_click`, `double_click`, `middle_click`, `drag`, `scroll` |
| 键盘 | `type_text`, `press_key`, `hold_key` |
| 定时 | `wait` |
| 浏览器 | `open_url`, `new_tab`, `close_tab`, `back`, `forward`, `reload` |
| 兜底 | `run_shell` |

## 让 LLM 自动部署

想把「克隆仓库 + 安装 + 启动 + 冒烟测试」整套交给一个代理完成?把 [docs/LLM_SETUP_PROMPT.md](docs/LLM_SETUP_PROMPT.md) 里的提示语整段复制给你的 LLM 代理即可。

## 演示提示词

[`examples/demo_prompts.md`](examples/demo_prompts.md) 里有 10 条由浅入深的提示,最核心的一条:

> *"用 computer_use 打开 Chrome、到 Google 搜索「snp500」,然后从结果页读取并告诉我当前 S&P 500 指数的价格。"*

运行时建议同时打开 `http://localhost:6080/vnc.html`,可以实时观看代理的每一步操作。

## 文档

- [WSL_SETUP.md](docs/WSL_SETUP.md) — Windows 侧配置 / systemd / linger
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — 架构与设计取舍
- [CAPTCHA.md](docs/CAPTCHA.md) — 各类 CAPTCHA 的能力矩阵
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 常见故障与修复
- [FAQ.md](docs/FAQ.md) — Playwright 对比、anti-bot 的真相
- [SECURITY.md](SECURITY.md) — 威胁模型与加固清单

## 安全

这相当于给 LLM 一双手。底线:

- 跑在一次性 WSL 发行版里,别污染日常环境
- 代理不需要 shell 时,移除 `run_shell` 工具
- 不要在 `CU_PROFILE_DIR` 里留真实凭据

更多细节见 [SECURITY.md](SECURITY.md)。

## 许可证

MIT,详见 [LICENSE](LICENSE)。
