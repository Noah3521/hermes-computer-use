# hermes-computer-use

[English](README.md) · **日本語** · [中文](README.zh.md) · [한국어](README.ko.md)

[![CI](https://github.com/Noah3521/hermes-computer-use/actions/workflows/ci.yml/badge.svg)](https://github.com/Noah3521/hermes-computer-use/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hermes-computer-use.svg)](https://pypi.org/project/hermes-computer-use/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: WSL2 Ubuntu](https://img.shields.io/badge/platform-WSL2%20Ubuntu-0078D6?logo=ubuntu&logoColor=white)](docs/WSL_SETUP.md)

> **対応環境:Windows 11 + WSL2 Ubuntu 22.04 / 24.04 のみ。** 詳細は [docs/WSL_SETUP.md](docs/WSL_SETUP.md)。

**ピクセル単位のブラウザ自動化 MCP サーバー。** MCP クライアント(hermes-agent、Claude Code、Codex など)に 21 個のツールを提供し、Xvfb ディスプレイ上で動く実際の Chrome を操作します。入力はスクリーンショット(ビジョン)、出力は OS レベルのマウス・キーボード。**CDP なし、`navigator.webdriver` なし、DOM ショートカットなし。**

<p align="center"><img src="docs/assets/demo-snp500.gif" width="760" alt="エージェントが Chrome を開き、Google 検索窓に「snp500」と入力して Enter。Google が通常の検索結果ページと S&P 500 指数カードを返す。すべてピクセルスクリーンショットと xdotool で実行。"></p>

> **デモの内容** — エージェントが Chrome を起動し、Google 検索窓にフォーカスして `snp500` を入力、Enter を押すと、S&P 500 のライブクオートカード付きの通常 SERP が返ってきます。同じフローは Playwright だと「異常なトラフィック」や CAPTCHA で止められがちですが、このスタックはスタックの Chrome + X11 入力という素のシグネチャなので検出されません。

## なぜ必要か

| | Playwright / CDP | hermes-computer-use |
|---|---|---|
| `navigator.webdriver` | `true`(検出可能) | `undefined` |
| CDP エンドポイント | 開放 | なし |
| DOM アクセス | 直接(速いが壊れやすい) | スクリーンショットのみ(遅いが UI リライトに強い) |
| Anti-bot の足跡 | 大きい、常にパッチ必要 | ほぼゼロ:素の Chrome + 素の X 入力 |
| 得意分野 | 自分で所有するサイトのフロー | 未知のサイトを人間のように操作するエージェント |

Cloudflare / Kasada / reCAPTCHA / DataDome で守られたサイトのフローを歩かせる必要があるときに、Playwright が止められる場面でも通ることが多いです。

## インストール

前提:Windows 11、WSL2 に Ubuntu 22.04/24.04、systemd 有効化。詳細は [docs/WSL_SETUP.md](docs/WSL_SETUP.md)。

以下はすべて **WSL シェル内** で実行します。

```bash
# PyPI から
pip install "hermes-computer-use[novnc]"

# またはソースから
git clone https://github.com/Noah3521/hermes-computer-use.git ~/hermes-computer-use
cd ~/hermes-computer-use
bash scripts/setup.sh                       # apt + Chrome (sudo)
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[novnc]"
mkdir -p ~/.config/systemd/user
cp systemd/*.example ~/.config/systemd/user/
sudo loginctl enable-linger "$USER"
systemctl --user daemon-reload
systemctl --user enable --now computer-use.service
```

スモークテスト:`python examples/smoke_test.py`

## ツール一覧(21)

| カテゴリ | ツール |
|---|---|
| 状態 | `screen_info`, `cursor_position` |
| キャプチャ | `screenshot` |
| ポインタ | `move`, `left_click`, `right_click`, `double_click`, `middle_click`, `drag`, `scroll` |
| キーボード | `type_text`, `press_key`, `hold_key` |
| タイミング | `wait` |
| ブラウザ | `open_url`, `new_tab`, `close_tab`, `back`, `forward`, `reload` |
| エスケープ | `run_shell` |

## LLM への自動セットアップ指示

エージェントに丸ごとセットアップ + スモークテストまで任せたい場合:[docs/LLM_SETUP_PROMPT.md](docs/LLM_SETUP_PROMPT.md) のプロンプトをコピーしてそのまま貼り付けてください。

## デモプロンプト

[`examples/demo_prompts.md`](examples/demo_prompts.md) にすぐ試せるプロンプト 10 本。一番シンプルなもの:

> *"computer_use を使って Chrome で Google を開き、「snp500」を検索して、結果ページに出る S&P 500 指数の現在値を教えて。"*

実行中は `http://localhost:6080/vnc.html` をブラウザで開いておくと、エージェントの操作がリアルタイムで見えます。

## ドキュメント

- [WSL_SETUP.md](docs/WSL_SETUP.md) — Windows 側セットアップ / systemd / linger
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — 内部構造と設計判断
- [CAPTCHA.md](docs/CAPTCHA.md) — 各 CAPTCHA カテゴリでの動作表
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — よくある障害と対処
- [FAQ.md](docs/FAQ.md) — Playwright 比較、anti-bot の現実など
- [SECURITY.md](SECURITY.md) — 脅威モデルとハードニング

## セキュリティ

LLM に手を持たせる行為です。少なくとも:

- 使い捨ての WSL ディストロで動かす(日常環境では動かさない)
- エージェントがシェルを必要としないなら `run_shell` は外す
- `CU_PROFILE_DIR` に本物の認証情報を入れない

詳細は [SECURITY.md](SECURITY.md)。

## ライセンス

MIT。[LICENSE](LICENSE) を参照。
