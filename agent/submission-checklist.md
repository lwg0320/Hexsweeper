# Agent-team evidence checklist

## Prepared artifacts

- [x] Implementation-agent instructions are prepared in [`AGENTS.md`](../AGENTS.md); the current Codex task locator is in [`AGENT-TEAM.md`](../AGENT-TEAM.md) and [`agent/config.json`](config.json).
- [x] Reusable skill is present at [`hex-minesweeper-player`](../hex_minesweeper/skills/hex-minesweeper-player/SKILL.md).
- [x] Existing independent-review report and read-only prompt are present in [`REVIEW.md`](REVIEW.md) and [`independent-review.md`](independent-review.md).
- [x] A factual team-log scaffold lists roles, access, recommendations, decisions, and evidence in [`AGENT-TEAM.md`](../AGENT-TEAM.md).

## Evidence still needed for a complete submission

- [ ] Place the complete project in the course repository at `midterms/lwg0320/`; the current checkout is the personal `lwg0320/Hexsweeper` repository at its root.
- [ ] Include the prepared workflow as `.github/workflows/midterm-lwg0320.yml` in the course PR. It is scoped to `midterms/lwg0320/**`; do not include another unrelated workflow change in that PR.
- [ ] Tag the final course PR game commit, then verify setup, play, tests, and evaluation from a fresh clone of that tagged commit using the README commands.
- [ ] Update the README commands so each says to run from `midterms/lwg0320/`.
- [ ] Update the Week 3 discussion header/thread with the Minesweeper-on-hexes scope change from the earlier Poolshark direction.
- [ ] Run the observation-only model and bounded-history model against the same three declared seeds, two trials each, and run both on held-out seeds. Record live outcomes, failures, limits, illegal moves, latency, tokens, dated cost, model/config, and final game commit in `EVALUATION.md`.
- [ ] Complete one live model episode with an action trace. The recording-only page mode is `/?recording=model`; the regular game page continues to show the deterministic Game playing agent.
- [ ] Have another person play the build while you watch without helping. Fill [`PLAYTEST-NOTES.md`](../PLAYTEST-NOTES.md) anonymously, or explain in `EVALUATION.md` why it was impossible and what a playtest would check.
- [ ] Make and link a three-to-five-minute recording showing the model agent playing without manual move selection and stating its limits. Use [`RECORDING-CHECKLIST.md`](../RECORDING-CHECKLIST.md).
- [ ] Add the recording link to the README and course PR description.
- [ ] Invoke `hex-minesweeper-player` by exact name in two distinct Codex sessions, use it on public observation/action data, and add both links and brief usage details to [`skill-usage.md`](skill-usage.md). Two turns in one chat or automatic file loading do not count as two sessions.
- [x] A separate read-only Codex subagent reviewed the current diff and confirmed the fixes; the scope, findings, and limits are in [`REVIEW.md`](REVIEW.md).
- [ ] The course's Codex evidence specifically asks for a separate CLI/cloud review session. If required, run that fresh read-only session with no instruction to approve, link it in the PR, and record the real link in [`agent/config.json`](config.json); do not treat this subagent report as a CLI/cloud session link.
- [ ] Rewrite the full one-page team log in the student's own voice, including each role's access, recommendation, decision, and evidence location. Use the real human playtest notes; do not submit the agent-written scaffold as the final log.
- [ ] After pushing the submission branch and opening the course PR, add the implementation-session link and links to `AGENTS.md`, the skill-use evidence, review, and team log to the PR description. A paste-ready block is in [`pr-body-template.md`](pr-body-template.md). The current Codex task has an in-app locator in `AGENT-TEAM.md`; a PR has not been linked here.
- [ ] Commit and push the current worktree changes so the prepared `AGENTS.md`, evidence guidance, and recent game updates are actually present in the GitHub repository.
- [ ] After assignments arrive on November 9, complete the three silent peer reviews in [`SILENT-PEER-REVIEWS.md`](../SILENT-PEER-REVIEWS.md) before class November 16. This is after the November 7 PR deadline.
