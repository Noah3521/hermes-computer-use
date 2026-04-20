# CAPTCHA & bot-detection capability

Pixel-level automation + clean fingerprint + human-like input = most detection stacks treat the browser as a normal human session. This doc catalogs what actually works, where the limits are, and where to test.

> **Ethics reminder.** All links below are dedicated test / demo pages. Use them for capability research, not to bypass production systems you're not authorized to access.

## Passive detection (fingerprint panels)

No challenge shown — the page just decides "bot or not" from headers, JS probes, canvas, WebGL, and timing. Our stack passes most of these by default because it runs stock Chrome with no CDP attached.

| Test page | Result | Notes |
|---|---|---|
| [bot.sannysoft.com](https://bot.sannysoft.com) | 🟢 all green except `WebGL Vendor/Renderer` | WebGL red is a side-effect of `--disable-gpu`. Most detectors accept "software renderer". |
| [abrahamjuliot.github.io/creepjs](https://abrahamjuliot.github.io/creepjs/) | 🟢 trust score in normal range | No Selenium/Playwright markers surfaced. |
| [pixelscan.net](https://pixelscan.net) | 🟢 consistent profile | IP geolocation dominates; use a residential proxy if you care about that column. |
| [fingerprint.com/demo](https://fingerprint.com/demo/) | 🟡 commercial product, sometimes flags | Fingerprint.com's own stack is closer to "enterprise" tier. |
| [browserscan.net/bot-detection](https://www.browserscan.net/bot-detection) | 🟢 browser=human | — |
| [arh.antoinevastel.com/bots/areyouheadless](https://arh.antoinevastel.com/bots/areyouheadless) | 🟢 "not headless" | Because we're genuinely headful under Xvfb, not using `--headless`. |
| Google search under load | 🟢 no captcha | Works cleanly from WSL IPs in Korea; expect "unusual traffic" on shared cloud IPs. |

## Interactive challenges

### Clickbox / score-based

| Type | Works? | Mechanism |
|---|---|---|
| **reCAPTCHA v2 "I'm not a robot" checkbox** | ✅ Usually silent pass | Eased-cubic mouse + clean fingerprint + stable timing = score high enough to skip image challenge. Demo: [google.com/recaptcha/api2/demo](https://www.google.com/recaptcha/api2/demo) |
| **reCAPTCHA v3** (invisible score) | ✅ Score normally 0.7–0.9 | Purely passive; no action needed. Keep the Chrome profile warm (cookies) for higher scores. |
| **Cloudflare Turnstile** | ✅ Passes automatically | Behavior + env probes only; no visible challenge for clean fingerprints. Demo: [demos.cloudflare.com/turnstile](https://demos.cloudflare.com/turnstile) |
| **hCaptcha invisible** | ✅ Usually pass | Same posture as Turnstile. |

### Vision-grid ("select all traffic lights")

| Type | Works? | Pattern |
|---|---|---|
| **reCAPTCHA v2 image challenge** | ✅ with vision model | `screenshot → VLM identifies cells → multiple left_click → verify_button`. 10–30 s. |
| **hCaptcha 3×3 / 4×4** | ✅ with vision model | Same pattern. Occasionally has semantic labels the model doesn't know ("crosswalk" vs "pedestrian crossing"); 1 retry usually succeeds. Demo: [accounts.hcaptcha.com/demo](https://accounts.hcaptcha.com/demo) |
| **Enterprise hCaptcha (rotating dynamic grids)** | ⚠️ ~60–80% | Images get harder; accuracy drops. |

### Slide CAPTCHAs (the one you asked about)

**Yes — theoretically and in practice it works.** Mechanics:

1. `screenshot` the challenge frame.
2. Vision model identifies:
   - the **puzzle piece** (small cut-out near the left edge)
   - the **gap** in the background where it fits
3. Compute `delta_x = gap.x − piece.x`.
4. Call `drag(piece.x, piece.y, piece.x + delta_x, piece.y, steps=30)`.

Our `drag()` uses eased-cubic interpolation with pixel-level jitter — that's exactly what GeeTest's behavioral classifier looks for (non-linear speed, non-zero acceleration variance). Straight-line drags get rejected; our drags mimic a human's.

| Variant | Works? | Notes |
|---|---|---|
| **GeeTest v3 slide puzzle** | ✅ High success | Demo: [2captcha.com/demo/geetest](https://2captcha.com/demo/geetest) |
| **GeeTest v4** | ⚠️ Medium | Adds stronger behavioral fingerprinting; use `CU_INPUT=ydotool` for `/dev/uinput` kernel-level input, add longer pre-click idle. Demo: [2captcha.com/demo/geetest-v4](https://2captcha.com/demo/geetest-v4) |
| **Tencent/Bilibili slider** | ✅ | Same shape as GeeTest. |
| **Custom slide** (jQuery plugins) | ✅ Easy | Usually just threshold-based; any smooth drag passes. |

### Rotate / orientation (Arkose Labs / FunCaptcha)

| Type | Works? | Notes |
|---|---|---|
| **"Pick the upright animal"** | ✅ with vision model | Screenshot → vision picks correct image → click. Drag-to-rotate variant: vision estimates target angle → drag arc. |
| **Enterprise Arkose** | ⚠️ | 3D rendering + behavioral telemetry; success rate falls. |

### Text CAPTCHA (legacy)

| Type | Works? |
|---|---|
| Distorted text | ✅ Trivial with any modern VLM |
| Math problem ("2 + 3 = ?") | ✅ Trivial |

### Audio challenge

⚠️ Not built into this stack. Would require: route Xvfb audio to PulseAudio → capture with `parec` → send to Whisper / speech-to-text → type answer. PR-worthy, not implemented.

## Sample prompt: solve a GeeTest v3 slide

```
Open https://2captcha.com/demo/geetest and solve the slide captcha:

1. screenshot the current page
2. Click "Click to verify" button (find coordinates in screenshot)
3. wait(1500)
4. screenshot — the puzzle challenge should now be visible
5. Identify in that screenshot:
   - the puzzle piece (small cutout shape near the left side)
   - the gap in the main image where the piece fits
6. Compute horizontal offset = gap_x − piece_x
7. Call drag(piece_x, piece_y, piece_x + offset, piece_y, steps=35)
8. wait(2000)
9. screenshot and report whether it says "Verification passed" or failed
```

## What improves success rate

| Lever | Effect |
|---|---|
| Warm Chrome profile (cookies, history) | Big — reputation signals |
| Residential / mobile IP | Enormous for IP-reputation-heavy sites |
| `CU_INPUT=ydotool` | Escalation for enterprise anti-bot (kernel-level HID) |
| `CU_KEY_DELAY_MS=40–60` | Types more human, helps with typing-speed classifiers |
| `CU_MOVE_STEPS=25+` | More interpolation points; smoother drags |
| Don't auto-click as soon as page loads | Add `wait(1000–3000)` before first action |

## What this project does **not** do

- No pre-packaged CAPTCHA solver. The agent (gpt-5.4, Claude, whatever) plus its vision capability is the solver. This repo just gives it the means to screenshot, think, and act.
- No audio routing.
- No IP rotation / proxy chaining. Handle that upstream in Chrome args (`--proxy-server=…`) or via system-level routing.
- No paid solver integration (2captcha/anticaptcha). Out of scope.
