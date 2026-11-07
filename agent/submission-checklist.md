# Agent-team evidence checklist

## Prepared artifacts

- [x] Implementation-agent instructions are prepared in [`AGENTS.md`](../AGENTS.md); the current Codex task locator is in [`AGENT-TEAM.md`](../AGENT-TEAM.md) and [`agent/config.json`](config.json).
- [x] Reusable skill is present at [`hex-minesweeper-player`](../hex_minesweeper/skills/hex-minesweeper-player/SKILL.md).
- [x] A fresh independent-review report and its read-only prompt are present in [`REVIEW.md`](REVIEW.md) and [`independent-review.md`](independent-review.md); the report covers the current Claude integration and records the reviewer's findings and author dispositions.
- [x] The one-page first-person agent-team log records each role's access, recommendation, decision, and evidence location in [`AGENT-TEAM.md`](../AGENT-TEAM.md).

## Evidence still needed for a complete submission

- [x] Staged the complete project in `midterms/lwg0320/` on local course branch `lwg0320/midterm`, based on freshly fetched `origin/main`; the local branch has not been pushed.
- [x] Copied only `.github/workflows/midterm-lwg0320.yml` to the course repository root; it is scoped to `midterms/lwg0320/**` and includes the deterministic and JavaScript checks.
- [x] From a fresh local clone of the course branch, setup required no installs, the website returned HTTP 200, all 45 tests passed on Python 3.8.0, JavaScript syntax passed, and the baseline completed all 10 evaluation episodes. A one-seed live smoke also ran both players; GitHub Actions still needs the pushed PR.
- [x] README commands state that the course-repository working directory is `midterms/lwg0320/` for setup, play, tests, and evaluation; the development checkout uses its root.
- [x] README scope statement identifies the Minesweeper-on-hexes scope change from the earlier Poolshark direction and names the first cuts.
- [x] Local verification on 2026-11-06: 45 unit tests passed on Python 3.8.0; browser JavaScript syntax and whitespace checks passed; the status endpoint is tested with both configured and blank Claude keys. This is not a GitHub Actions result.
- [x] The paired final trace contains the 10 deterministic baseline episodes alongside both model configurations; the earlier one-episode acceptance trace is [`evaluation/baseline-smoke-2026-10-26.jsonl`](../evaluation/baseline-smoke-2026-10-26.jsonl).
- [x] Posted the scope change as a reply to the original Week 3 post on November 6, 2026; the reply link and text are recorded in [`WEEK3-SCOPE-UPDATE.md`](../WEEK3-SCOPE-UPDATE.md).
- [x] The revised human-playtest item accepts any person playing your build; an anonymous friend played all three sizes while you watched without helping. The notes in [`PLAYTEST-NOTES.md`](../PLAYTEST-NOTES.md) cover what they tried, where they hesitated, their difficulty impression, and a possible change. A partner playing someone else's build is not needed to satisfy this item.
- [x] Reran the observation-only and bounded-history models on the same three declared and two held-out seeds, two trials each. Current results, failures, limits, illegal moves, latency, tokens, dated cost, model/config, and the 30-episode trace are in [`EVALUATION.md`](../EVALUATION.md). Game and test code match revision `0bb8a0a`; the trace marks the documentation-only working tree dirty.
- [x] The live model comparison contains individual Claude API episodes and action traces. The recording is separate evidence: it visibly shows the deterministic Game playing agent running automatically, and also includes a Claude API-agent episode.
- [x] A 4:52, 44.3 MB compressed MP4 is present at [`hexsweeper-recording.mp4`](../hexsweeper-recording.mp4); sampled frames confirm automatic deterministic-agent actions and a mine-hit ending.
- [x] Owner confirmed on 2026-11-06 that the recording narration states the agent's limits (public information only, may need to guess, 80-decision cap); see [`RECORDING-CHECKLIST.md`](../RECORDING-CHECKLIST.md).
- [x] The video link is in the README and the PR-body template has direct links for the local `lwg0320/midterm` course branch in [`pr-body-template.md`](pr-body-template.md).
- [ ] After opening the course PR, verify the recording URL opens for instructors, TAs, and assigned peer reviewers; update owner/repository/branch in the link if needed.
- [x] Invoke `hex-minesweeper-player` by exact name in two distinct Codex sessions, use it on public observation/action data, and add both links and brief usage details to [`skill-usage.md`](skill-usage.md). Two turns in one chat or automatic file loading do not count as two sessions.
- [x] Complete the declared and held-out live provider trials using the Anthropic Claude API adapter. Mocked responses verify the application but do not count as live model trials; the paired live traces are linked in [`EVALUATION.md`](../EVALUATION.md).
- [x] Not applicable: live Claude API access was available and the full declared and held-out comparison was completed; no reduced-suite exception is needed.
- [x] Commission a fresh independent read-only review of the current Claude API, key-status UI, retry/fallback handling, information boundaries, limits, and documentation.
- [x] Capture the reviewer's actual session link and findings in [`REVIEW.md`](REVIEW.md) and [`agent/config.json`](config.json). The reviewer did not write the code and received no instruction to approve it.
- [x] Replaced the scaffold with a concise first-person log based on the user's recorded decisions, skill sessions, review, evaluation, and playtest notes in [`AGENT-TEAM.md`](../AGENT-TEAM.md).
- [ ] Push the local course branch, open the PR, paste the prepared project and agent-team evidence links from [`pr-body-template.md`](pr-body-template.md), verify the recording URL is accessible, and add the passing Actions link. The PR is not open yet.
- [x] The personal Hexsweeper repository is separate from the course hand-in. Keep subsequent changes local unless the user explicitly requests another push; a personal-repository URL is not a submission.
- [ ] After assignments arrive on November 9, complete the three silent peer reviews in [`SILENT-PEER-REVIEWS.md`](../SILENT-PEER-REVIEWS.md) before class November 16. This is after the November 7 PR deadline.
