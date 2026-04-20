# hermes-computer-use

[English](README.md) · [日本語](README.ja.md) · [中文](README.zh.md) · **한국어**

[![CI](https://github.com/Noah3521/hermes-computer-use/actions/workflows/ci.yml/badge.svg)](https://github.com/Noah3521/hermes-computer-use/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/hermes-computer-use.svg)](https://pypi.org/project/hermes-computer-use/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: WSL2 Ubuntu](https://img.shields.io/badge/platform-WSL2%20Ubuntu-0078D6?logo=ubuntu&logoColor=white)](docs/WSL_SETUP.md)

> **지원 환경: Windows 11 + WSL2 Ubuntu 22.04 / 24.04 전용.** 자세한 설정은 [docs/WSL_SETUP.md](docs/WSL_SETUP.md).

**픽셀 단위 브라우저 자동화 MCP 서버.** MCP를 말하는 모든 클라이언트(hermes-agent, Claude Code, Codex 등)에 21개 도구를 제공하여 Xvfb 가상 디스플레이 위의 실제 Chrome을 조작합니다. 입력은 스크린샷(비전), 출력은 OS 레벨 마우스/키보드. **CDP 없음. `navigator.webdriver` 없음. DOM 쇼트컷 없음.**

<p align="center"><img src="docs/assets/demo-snp500.gif" width="760" alt="에이전트가 Chrome을 열고 Google 검색창에 'snp500'을 입력한 뒤 Enter를 누르자 Google이 S&P 500 실시간 시세 카드가 포함된 정상 결과 페이지를 반환. 전 과정이 픽셀 스크린샷 + xdotool로 이뤄짐."></p>

> **GIF 설명** — 에이전트가 Chrome을 실행하고 Google 검색창에 포커스, `snp500` 입력, Enter. Google이 S&P 500 실시간 카드까지 포함된 정상 SERP를 반환합니다. 같은 흐름을 Playwright로 돌리면 "비정상 트래픽" 페이지나 캡챠에 자주 막히는데, 이 스택은 순수 Chrome + 순수 X11 입력이라 자동화 지문이 없어 걸리지 않습니다.

## 왜 만들었나

| | Playwright / CDP | hermes-computer-use |
|---|---|---|
| `navigator.webdriver` | `true` (탐지됨) | `undefined` |
| CDP 엔드포인트 | 열려 있음 | 없음 |
| DOM 접근 | 직접 (빠르지만 UI 변경에 취약) | 스크린샷만 (느리지만 UI 리라이트에 견고) |
| Anti-bot 지문 | 큼, 지속 패치 필요 | 거의 제로: 순수 Chrome + 순수 X 입력 |
| 적합한 경우 | 자기가 소유한 사이트의 안정 플로우 | 에이전트가 낯선 사이트를 사람처럼 조작 |

Cloudflare · Kasada · reCAPTCHA · DataDome에 막히는 회원가입/로그인 퍼널을 사람처럼 걸어야 할 때 유용합니다.

## 설치

전제: Windows 11, WSL2 + Ubuntu 22.04/24.04, systemd 활성화. 전체 가이드는 [docs/WSL_SETUP.md](docs/WSL_SETUP.md).

모든 명령은 **WSL 쉘 안에서** 실행합니다.

```bash
# PyPI에서
pip install "hermes-computer-use[novnc]"

# 또는 소스에서
git clone https://github.com/Noah3521/hermes-computer-use.git ~/hermes-computer-use
cd ~/hermes-computer-use
bash scripts/setup.sh                       # 시스템 패키지 + Chrome (sudo)
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[novnc]"
mkdir -p ~/.config/systemd/user
cp systemd/*.example ~/.config/systemd/user/
sudo loginctl enable-linger "$USER"
systemctl --user daemon-reload
systemctl --user enable --now computer-use.service
```

스모크 테스트: `python examples/smoke_test.py`

## 도구 (21개)

| 구분 | 도구 |
|---|---|
| 상태 | `screen_info`, `cursor_position` |
| 캡처 | `screenshot` |
| 포인터 | `move`, `left_click`, `right_click`, `double_click`, `middle_click`, `drag`, `scroll` |
| 키보드 | `type_text`, `press_key`, `hold_key` |
| 대기 | `wait` |
| 브라우저 | `open_url`, `new_tab`, `close_tab`, `back`, `forward`, `reload` |
| 비상탈출 | `run_shell` |

## LLM에 맡겨서 자동 세팅

클론 → 설치 → 서비스 기동 → 스모크까지 한 번에 에이전트에게 시키고 싶다면, [docs/LLM_SETUP_PROMPT.md](docs/LLM_SETUP_PROMPT.md) 내용을 그대로 복사해 LLM에게 전달하세요.

## 데모 프롬프트

[`examples/demo_prompts.md`](examples/demo_prompts.md)에 10개의 난이도별 프롬프트가 있습니다. 가장 간단한 것:

> *"computer_use로 Chrome을 열고 Google에서 'snp500' 검색한 뒤, 결과 페이지의 현재 S&P 500 지수 가격을 알려줘."*

실행 중 `http://localhost:6080/vnc.html`을 브라우저로 열어두면 에이전트의 조작이 실시간으로 보입니다.

## 문서

- [WSL_SETUP.md](docs/WSL_SETUP.md) — Windows 쪽 세팅 / systemd / linger
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — 내부 구조와 설계 근거
- [CAPTCHA.md](docs/CAPTCHA.md) — 캡챠 카테고리별 동작 매트릭스
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — 흔한 장애 + 해결법
- [FAQ.md](docs/FAQ.md) — Playwright 비교, anti-bot 현실 등
- [SECURITY.md](SECURITY.md) — 위협 모델 + 하드닝 체크리스트

## 보안

LLM에게 손을 주는 일입니다. 최소한:

- 일회용 WSL 배포판에서만 실행 (일상 환경에서 돌리지 마세요)
- 에이전트가 쉘이 필요 없으면 `run_shell` 도구 제거
- `CU_PROFILE_DIR`에 실제 자격정보 저장 금지

자세한 내용은 [SECURITY.md](SECURITY.md).

## 라이선스

MIT. [LICENSE](LICENSE) 참조.
