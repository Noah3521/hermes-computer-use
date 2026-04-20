# Demo prompts

Paste these into any MCP client connected to `computer_use`. Ordered smoke → real-world.

## 1. Sanity (5 seconds)

```
Use computer_use to call screen_info and screenshot. Describe what's on the virtual display.
```

## 2. Google search — the headline demo

```
Use computer_use to open Chrome, type "snp500" into the Google search bar, press Enter, take
a screenshot, and tell me the current S&P 500 index price that appears on the results page.
```

Playwright would often get "unusual traffic" or a reCAPTCHA on this flow. This stack doesn't
because the browser is stock Chrome, input is stock X11. If you do see a block, it's IP-based
reputation, not our fingerprint.

## 3. Read a news site

```
Use computer_use to open https://news.ycombinator.com and list the titles of the top three
stories, with the point count for each.
```

## 4. Coordinate-grounded click

```
Use computer_use to open https://example.com and click the "More information..." link
using pixel coordinates from the screenshot (no DOM). Report the title of the destination page.
```

## 5. Search + read

```
Use computer_use to open https://duckduckgo.com, click the search box, type "WSL2 wayland xvfb",
press Enter, and give me the titles of the first three results.
```

## 6. Scroll

```
Use computer_use to open https://en.wikipedia.org/wiki/Xvfb and scroll down three times,
screenshotting between each scroll. List the section headings you passed.
```

## 7. Drag — a slider

```
Use computer_use to open https://www.w3schools.com/howto/howto_js_rangeslider.asp and drag the
slider in the "Try it Yourself" panel all the way to the right. Report the final displayed value.
```

## 8. Form login (public test site)

```
Use computer_use to open https://the-internet.herokuapp.com/login and log in with username
"tomsmith" and password "SuperSecretPassword!". Screenshot the page after submit and report
the success message text.
```

## 9. Bot-detection panel

```
Use computer_use to open https://bot.sannysoft.com, take a screenshot, and summarise which
detection checks passed (green) and which failed (red).
```

## 10. Shell escape hatch

```
Use computer_use's run_shell tool to run `xdpyinfo -display :99 | grep dimensions` and
print the output verbatim.
```
