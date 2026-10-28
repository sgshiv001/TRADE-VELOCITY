# TradeVelocity v0.3.4 — Windows pre-release

**Published 28 October 2026 as an unsigned pre-release for testing.**

[Download the Windows x64 package](https://github.com/sgshiv001/TRADE-VELOCITY/releases/tag/v0.3.4).

## What changed

- The Overview now includes an animated CSS 3D view of the selected symbol's
  actual local order-book depth. Sell and buy depth are separated by side; best
  ask, best bid, and last matched price remain visible as readable values.
- Empty books show an explicit empty state instead of invented market activity.
- The primary “Place an order” action is prominent. Controls use larger targets,
  and the layout adapts to smaller screens while keeping light and dark themes.
- Smooth page transitions and staggered cards clarify navigation; hover and focus
  feedback adds motion without obscuring trading controls.
- The Windows executable and native window use a multiresolution TradeVelocity
  icon. The desktop launcher shows a short animated intro while the local engine
  and workspace connect, then fades into the working app. The startup display
  reports the connection state and states that the app is simulation-only.
- Reduced-motion settings disable decorative animation and smooth scrolling.
- Theme/watchlist preferences remain usable when browser storage is blocked.
- Live updates stop polling while offline and reconnect when the network returns.

## Verification status

On 28 October, the production frontend build passed, **160 Python tests** and
**13 Playwright browser tests** passed, and the rebuilt Windows app passed its
isolated native smoke test. The packaged smoke verified the actual Windows
window icon, startup handoff, matching, live updates, AI calibration, and the
high-volume regression. Browser coverage also checks reduced motion, themes,
order lifecycle, AI review, reconnection, and responsive layouts. Manual
acceptance on the user's PC and testing on another PC remain pending;
code-signing status is unchanged.

This is an unsigned Windows x64 pre-release. It requires Windows 10/11
x64, WebView2 Evergreen, and .NET Framework 4.6.2 or newer. Orders stay in the
local matching engine; no broker or real-money execution is involved.
