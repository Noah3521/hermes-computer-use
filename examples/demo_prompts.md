# Demo Prompts for hermes

Prompts that exercise the `computer_use` MCP tools, ordered from smoke → real-world.

## 1. Sanity (5s)
```
computer_use 서버의 screen_info와 screenshot 툴을 호출해서 지금 화면 상태를 알려줘.
```

## 2. Static navigation
```
computer_use로 https://news.ycombinator.com 에 접속해. 로드 끝나면 screenshot 다시
찍어서 첫 번째 기사 제목을 알려줘.
```

## 3. Coordinate-grounded click
```
https://example.com 을 연 뒤, 페이지 하단의 "More information..." 링크를
screenshot으로 좌표 찾아서 클릭해. 클릭 후 이동한 페이지 제목을 알려줘.
```

## 4. Search & read
```
https://duckduckgo.com 을 열고 검색창을 클릭한 다음 "WSL2 wayland xvfb" 라고
타이핑해서 검색 결과 첫 3개 제목을 읽어줘.
```

## 5. Scroll
```
https://en.wikipedia.org/wiki/Xvfb 을 열고 페이지를 3번 스크롤 다운해줘. 각
스크롤 후 screenshot 찍고 현재 섹션 제목이 뭔지 순서대로 말해줘.
```

## 6. Drag / slider
```
https://www.w3schools.com/howto/howto_js_rangeslider.asp 을 열고 Try it Yourself
패널의 슬라이더를 drag해서 오른쪽 끝까지 밀어줘. 최종 값이 얼마인지 알려줘.
```

## 7. Form login (anti-bot friendly)
```
https://the-internet.herokuapp.com/login 에 접속해서 username "tomsmith",
password "SuperSecretPassword!" 로 로그인해줘. 성공 메시지가 뜨면 그 메시지
텍스트를 screenshot에서 읽어줘.
```

## 8. Bot detection panel
```
https://bot.sannysoft.com 을 열어서 screenshot 찍고, 어떤 detection 항목이
"passed" 또는 "failed"로 뜨는지 표로 정리해줘.
```

## 9. Google → external site → internal SSO (5-hop)
```
computer_use 서버로 아래 시나리오를 실행하고, 각 단계마다 screenshot을 찍은 뒤 무엇이
보이는지 간단히 보고해줘. 자동화 차단(captcha / "비정상 트래픽" / reCAPTCHA) 여부도 명시해.

1. open_url로 https://www.google.com 접속
2. 1500ms 대기 후 screenshot
3. 검색창을 screenshot에서 pixel 좌표로 찾아 left_click
4. type_text로 "인터파크 티켓" 입력 (delay_ms=40)
5. press_key("Return")
6. 2000ms 대기 후 screenshot — 최상단 결과 제목/URL 판독
7. 차단 없으면 최상단 공식 사이트 링크 클릭
8. 3000ms 대기 후 screenshot
9. 페이지 우측 상단 "로그인" 버튼 클릭
10. 1500ms 대기 후 screenshot — 로그인 페이지 진입 확인

가드레일: ID/PW 입력 금지. 로그인 페이지 진입까지가 최종. 스텝 간 최소 500ms.
```

## 10. Escape hatch
```
computer_use의 run_shell 툴로 `xdpyinfo -display :99 | grep dimensions` 실행한 결과를
그대로 출력해줘.
```
