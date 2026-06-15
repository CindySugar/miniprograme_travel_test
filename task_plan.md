# Task Plan

## Goal
Optimize the `创建猫猫组队` secondary page UI against the four supplied reference screenshots, covering the `组队`/`详情`/`高级` tabs and the scrolled advanced permission section.

## Phases

- [completed] 1. Read PRD, current create page, and relevant project conventions
- [completed] 2. Implement the three-tab create-team UI and basic interactions
- [completed] 3. Commit the initial PRD implementation with a clean git history
- [completed] 4. Tune the create page visual layout against the new screenshots
- [completed] 5. Verify with available WeChat DevTools / Playwright / Computer Use paths
- [in_progress] 6. Commit the UI optimization

## Notes

- Preserve the existing home page and trip detail flows.
- Prefer a page-scoped UI implementation; only touch `travel-store` if needed to persist members from the create flow.
- Added a root `.gitignore` so local generated state is not committed.
- WeChat DevTools direct pageframe access with Playwright is blocked by `PROXY_ERROR: invalid ua token`; CLI automation also requires enabling the IDE service port. Used Computer Use against the running WeChat DevTools simulator for visual checks, with temporary default-tab routing to verify the three tab states without committing those temporary defaults.
- Computer Use clicks on the simulator iframe showed hover/focus but did not reliably trigger mini program tap handlers. The final implementation keeps explicit button tab handlers, and each tab state was rendered in DevTools by temporarily setting the default active tab, then restored to `组队`.
- New visual targets:
  - `组队`: large rounded hero, pill tabs, compact title input, single team card with dashed separators, owner row, green hint, family dashed placeholder.
  - `详情`: same hero/tabs, a single details card near the top and large dotted empty space above the fixed CTA.
  - `高级`: rules card, separate permission rows, bottom CTA overlay; scrolled state reveals the third avatar-required switch.
