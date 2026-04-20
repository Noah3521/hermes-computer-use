# LLM Setup Prompt

Copy-paste the block below into any agentic LLM (Claude Code, OpenAI Codex, hermes-agent, Cursor, Aider, or anything with **shell + filesystem** tools) running inside a **WSL2 Ubuntu 22.04 / 24.04** shell. The agent will clone this repo, install it, start the virtual display stack, and run the smoke test without further guidance.

Language versions: **English** (below) · [日本語](#日本語) · [中文](#中文) · [한국어](#한국어)

---

## English

````
You are an automation agent running inside a WSL2 Ubuntu 22.04 or 24.04 shell. Your job
is to install and verify `hermes-computer-use` — an MCP server for pixel-level browser
automation — without asking the user to run commands manually.

Ground rules:
- Always run commands sequentially and print the exit status + relevant tail of stdout.
- When a step needs sudo, surface the sudo prompt to the user; do not attempt to bypass.
- Stop and report immediately if any step fails; do not silently retry the same command.
- After every step, summarise in one line what you did and whether it worked.

Steps:

1. Environment check
   - `uname -a`            # must contain "microsoft" or "WSL"
   - `lsb_release -is`     # must be "Ubuntu"
   - `systemctl is-system-running`  # must print "running" (enable systemd in /etc/wsl.conf if not)
   - Abort and tell the user if any of the three conditions fails.

2. Clone + install
   - `git clone https://github.com/Noah3521/hermes-computer-use.git ~/hermes-computer-use`
   - `cd ~/hermes-computer-use`
   - `bash scripts/setup.sh`       # apt packages + Chrome + uinput (needs sudo)

3. Python package
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e ".[novnc]"`

4. (Optional) browser-based observer
   - `bash scripts/install-novnc.sh`

5. Systemd user services
   - `mkdir -p ~/.config/systemd/user`
   - `install -m 0644 systemd/computer-use.service.example ~/.config/systemd/user/computer-use.service`
   - `install -m 0644 systemd/novnc.service.example ~/.config/systemd/user/novnc.service`
   - Edit the ExecStart paths in both files so they match the actual clone directory
     ($HOME/hermes-computer-use).
   - `sudo loginctl enable-linger "$USER"`
   - `systemctl --user daemon-reload`
   - `systemctl --user enable --now computer-use.service novnc.service`
   - `systemctl --user status computer-use.service --no-pager | head -15`

6. End-to-end smoke test
   - `python examples/smoke_test.py`
   - Expected output must include: a list of 21 tools, `screen_info` with the
     display geometry, a `screenshot` that returns non-zero base64 bytes, and
     a `cursor_position` response.

7. Final report
   Print a one-screen summary with: WSL distro + kernel, Chrome version, active
   service PIDs, the smoke test tool count, noVNC URL (http://localhost:6080/vnc.html),
   and any warnings.

If any step fails, dump the relevant logs before reporting:
- `journalctl --user -u computer-use.service -n 80 --no-pager`
- `tail -n 50 /tmp/hermes-computer-use/*.log 2>/dev/null`
- Cross-reference the failure with ~/hermes-computer-use/docs/TROUBLESHOOTING.md
  and propose the specific fix from that doc.
````

---

## 日本語

````
あなたは WSL2 Ubuntu 22.04 / 24.04 のシェル内で動く自動化エージェントです。
`hermes-computer-use`(ピクセル単位のブラウザ自動化 MCP サーバー)を
ユーザーに手作業を求めずにインストール・検証してください。

ルール:
- コマンドは順次実行し、終了コードと stdout の末尾を表示する
- sudo が必要な場面ではユーザーにプロンプトを見せる。勝手に回避しない
- 失敗したら即座に停止して報告し、同じコマンドを黙って再試行しない
- 各ステップ後に「何をしたか / 成功か」を 1 行で要約する

手順:

1. 環境確認
   - `uname -a`(「microsoft」または「WSL」を含む必要)
   - `lsb_release -is`(「Ubuntu」である必要)
   - `systemctl is-system-running`(「running」である必要)
   - 上記 3 つのどれかが満たされない場合は停止してユーザーに報告

2. クローン + 初期インストール
   - `git clone https://github.com/Noah3521/hermes-computer-use.git ~/hermes-computer-use`
   - `cd ~/hermes-computer-use`
   - `bash scripts/setup.sh`(apt + Chrome + uinput、sudo 必須)

3. Python パッケージ
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e ".[novnc]"`

4. (任意)ブラウザビューア
   - `bash scripts/install-novnc.sh`

5. systemd ユーザーサービス
   - `mkdir -p ~/.config/systemd/user`
   - `install -m 0644 systemd/computer-use.service.example ~/.config/systemd/user/computer-use.service`
   - `install -m 0644 systemd/novnc.service.example ~/.config/systemd/user/novnc.service`
   - ExecStart のパスを実際のクローン先($HOME/hermes-computer-use)に合わせて編集
   - `sudo loginctl enable-linger "$USER"`
   - `systemctl --user daemon-reload`
   - `systemctl --user enable --now computer-use.service novnc.service`

6. E2E スモークテスト
   - `python examples/smoke_test.py`
   - 期待出力:21 個のツールリスト、`screen_info` の解像度、非ゼロの base64 スクリーンショット、
     `cursor_position` の応答

7. 最終報告
   WSL ディストロ + カーネル、Chrome バージョン、アクティブなサービス PID、スモークテストの
   ツール数、noVNC URL(http://localhost:6080/vnc.html)、警告を 1 画面に収めて出力

失敗時は以下を吸い上げてから報告:
- `journalctl --user -u computer-use.service -n 80 --no-pager`
- `tail -n 50 /tmp/hermes-computer-use/*.log 2>/dev/null`
- `~/hermes-computer-use/docs/TROUBLESHOOTING.md` を参照して具体的な対処を提案
````

---

## 中文

````
你是运行在 WSL2 Ubuntu 22.04 / 24.04 shell 中的自动化代理。你的任务是安装并验证
`hermes-computer-use`(一个像素级浏览器自动化的 MCP 服务器),
全程不要让用户手动执行命令。

规则:
- 按顺序执行命令,打印退出码和 stdout 末尾
- 需要 sudo 时把提示显示给用户,不要试图绕过
- 任一步失败立刻停止并汇报,不要默默重试
- 每步结束后用一行总结做了什么、是否成功

步骤:

1. 环境检查
   - `uname -a`(必须包含「microsoft」或「WSL」)
   - `lsb_release -is`(必须是「Ubuntu」)
   - `systemctl is-system-running`(必须是「running」)
   - 任一项不满足就中止并告诉用户

2. 克隆 + 系统依赖
   - `git clone https://github.com/Noah3521/hermes-computer-use.git ~/hermes-computer-use`
   - `cd ~/hermes-computer-use`
   - `bash scripts/setup.sh`(apt + Chrome + uinput,需要 sudo)

3. Python 包
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e ".[novnc]"`

4. (可选)浏览器观察器
   - `bash scripts/install-novnc.sh`

5. systemd 用户服务
   - `mkdir -p ~/.config/systemd/user`
   - `install -m 0644 systemd/computer-use.service.example ~/.config/systemd/user/computer-use.service`
   - `install -m 0644 systemd/novnc.service.example ~/.config/systemd/user/novnc.service`
   - 编辑两个文件里的 ExecStart 路径,匹配实际克隆目录($HOME/hermes-computer-use)
   - `sudo loginctl enable-linger "$USER"`
   - `systemctl --user daemon-reload`
   - `systemctl --user enable --now computer-use.service novnc.service`

6. 端到端冒烟测试
   - `python examples/smoke_test.py`
   - 期望输出:21 个工具列表、`screen_info` 的分辨率、非零字节的 base64 截图、
     `cursor_position` 响应

7. 最终报告
   用一屏输出:WSL 发行版 + 内核、Chrome 版本、活跃的服务 PID、冒烟测试工具计数、
   noVNC 地址(http://localhost:6080/vnc.html)以及任何警告

失败时先抓取日志再汇报:
- `journalctl --user -u computer-use.service -n 80 --no-pager`
- `tail -n 50 /tmp/hermes-computer-use/*.log 2>/dev/null`
- 对照 `~/hermes-computer-use/docs/TROUBLESHOOTING.md` 提出具体修复方案
````

---

## 한국어

````
당신은 WSL2 Ubuntu 22.04 또는 24.04 쉘 안에서 동작하는 자동화 에이전트입니다.
`hermes-computer-use`(픽셀 단위 브라우저 자동화 MCP 서버)를 사용자에게 수동 실행을
요구하지 않고 설치·검증하세요.

규칙:
- 명령은 순차적으로 실행하고 exit code + stdout 꼬리를 출력한다
- sudo가 필요하면 사용자에게 프롬프트를 보여주고, 우회하지 않는다
- 단계 실패 시 즉시 중단·보고하고, 같은 명령을 조용히 재시도하지 않는다
- 각 단계 후 "무엇을 했는지 / 성공했는지"를 한 줄 요약한다

단계:

1. 환경 확인
   - `uname -a` ("microsoft" 또는 "WSL" 포함 필수)
   - `lsb_release -is` ("Ubuntu" 필수)
   - `systemctl is-system-running` ("running" 필수)
   - 셋 중 하나라도 실패하면 중단 + 사용자에게 알림

2. 클론 + 시스템 의존성
   - `git clone https://github.com/Noah3521/hermes-computer-use.git ~/hermes-computer-use`
   - `cd ~/hermes-computer-use`
   - `bash scripts/setup.sh` (apt + Chrome + uinput, sudo 필요)

3. Python 패키지
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e ".[novnc]"`

4. (선택) 브라우저 관찰기
   - `bash scripts/install-novnc.sh`

5. systemd 유저 서비스
   - `mkdir -p ~/.config/systemd/user`
   - `install -m 0644 systemd/computer-use.service.example ~/.config/systemd/user/computer-use.service`
   - `install -m 0644 systemd/novnc.service.example ~/.config/systemd/user/novnc.service`
   - 두 파일의 ExecStart 경로를 실제 클론 디렉토리($HOME/hermes-computer-use)에 맞춰 수정
   - `sudo loginctl enable-linger "$USER"`
   - `systemctl --user daemon-reload`
   - `systemctl --user enable --now computer-use.service novnc.service`

6. 종단 스모크 테스트
   - `python examples/smoke_test.py`
   - 기대 출력: 21개 툴 목록, `screen_info`의 해상도, 0이 아닌 base64 스크린샷 바이트,
     `cursor_position` 응답

7. 최종 보고
   한 화면에: WSL 배포판 + 커널, Chrome 버전, 서비스 PID, 스모크 툴 수,
   noVNC URL (http://localhost:6080/vnc.html), 경고사항

실패 시 먼저 로그를 덤프한 뒤 보고:
- `journalctl --user -u computer-use.service -n 80 --no-pager`
- `tail -n 50 /tmp/hermes-computer-use/*.log 2>/dev/null`
- `~/hermes-computer-use/docs/TROUBLESHOOTING.md`를 참고해 구체적 해결책 제안
````
