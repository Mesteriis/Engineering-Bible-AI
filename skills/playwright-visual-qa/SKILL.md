---
name: [be] playwright-visual-qa
description: "Проверяет отрендеренный frontend UI через browser или Playwright screenshots после UI implementation, redesign, Figma-to-code, image-to-code, responsive changes, visual regressions или сравнения с accepted reference."
---

# Playwright Visual QA

Verify the rendered UI, not just the build.

## Workflow

1. Read `ui-qa`.
2. Start or identify the local app URL.
3. Capture desktop and mobile screenshots.
4. Compare against the accepted concept, Figma frame, screenshot, or existing
   baseline.
5. Check layout, copy, typography, colors, assets, icons, states, and overflow.
6. Fix material drift when implementation is in scope.

## Output

- URL or app entrypoint
- screenshots/viewports checked
- reference used
- mismatches found
- fixes made or recommended
- remaining deviations

## Rule

Functional tests do not replace visual QA. If screenshots cannot be captured,
state the blocker.
