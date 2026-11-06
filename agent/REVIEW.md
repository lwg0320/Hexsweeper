# Independent review report

**Review date:** 2026-11-06
**Reviewer:** a separate Codex read-only subagent; it did not author or edit implementation code. A standalone Codex CLI/cloud session link was not captured, so add one if the course requires that exact evidence form.
**Review instructions:** [independent-review.md](independent-review.md)

## Scope and checks

The reviewer examined the current game/rules interface, runner and limits, model adapter, server routes, browser controls, map sizes, bounded history, tests, evaluation plan, source map, and submission evidence. It checked that preterminal observations and legal actions do not reveal seeds or mine positions; the model sees public observations/actions and, in history mode, only recent public actions/results. It also checked invalid moves, provider errors, timeouts, terminal reasons, recording-mode control wiring, and the README/CI commands.

The reviewer reported no direct preterminal seed or mine leak. The deterministic solver uses the same public interface as the model. Runner limits are explicit: 80 actions, 80 model calls, and a 20-second outer deadline; failed and invalid model turns have explicit outcomes. It noted that a provider worker is not cancelled after timeout and could finish later, although its result cannot mutate runner state and a delayed provider call could still incur cost.

## Findings and disposition

1. **Recording-mode API gate (P2):** The first review found that hiding the model button did not stop ordinary sessions from posting to `/api/model/step`. I added a `model_playback_enabled` session flag set by the recording-only page and required it at the route before making a provider call. A normal page session is rejected. The reviewer confirmed the reset wiring, UI, route, and regression check. This is an explicit opt-in for this local app, not an authentication boundary: a caller can create a session with the flag set directly.
2. **History cap:** The first review found that a custom caller could request more than the documented eight actions. `ModelAgent` and the runner now enforce a limit of one through eight; tests cover the upper bound. The reviewer confirmed the cap.
3. **Source-map wording:** The map now explains that size presets are the only map-size selector and there is no separate difficulty setting. The reviewer confirmed the clarification.

The reviewer found the KMines rule summary and Atari no-reuse statement consistent with the cited sources. The project does not reuse Poolshark code or Atari content.

## Verification and remaining limits

The read-only reviewer reported all 32 unit tests passing and `node --check hex_minesweeper/static/app.js` passing after the fixes. I separately viewed both the ordinary page and `/?recording=model`: the first shows only the deterministic Game playing agent; the recording view shows a live model Start control and warns that calls may use paid credits. No live provider call was made.

This review does not supply the missing live model comparison, human playtest, recording, two separate skill-invocation session links, student-authored team log, or a clean tagged course-repository clone. The reviewer could not verify those artifacts, and this report does not claim they exist. The model comparison still needs to report both model variants on the same declared and held-out cases, including failures, limits, latency, tokens, and dated cost.
