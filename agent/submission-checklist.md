# Agent-team evidence checklist

## Prepared artifacts

- [x] Implementation-agent instructions are prepared in [`AGENTS.md`](../AGENTS.md); the current Codex task locator is in [`AGENT-TEAM.md`](../AGENT-TEAM.md) and [`agent/config.json`](config.json).
- [x] Reusable skill is present at [`hex-minesweeper-player`](../hex_minesweeper/skills/hex-minesweeper-player/SKILL.md).
- [x] Existing independent-review report and read-only prompt are present in [`REVIEW.md`](REVIEW.md) and [`independent-review.md`](independent-review.md).
- [x] A factual team-log scaffold lists roles, access, recommendations, decisions, and evidence in [`AGENT-TEAM.md`](../AGENT-TEAM.md).

## Evidence still needed for a complete submission

- [ ] Place the complete project in the course repository at `midterms/lwg0320/`; the current checkout is the personal `lwg0320/Hexsweeper` repository at its root.
- [ ] Include the prepared workflow as `.github/workflows/midterm-lwg0320.yml` in the course PR. It is scoped to `midterms/lwg0320/**`; do not include another unrelated workflow change in that PR.
- [ ] Verify setup, play, tests, and evaluation from a fresh clone of the final course PR head using the README commands. The new brief says staff read the graded commit from the PR timeline; there is no need to name a commit or create a tag.
- [ ] Update the README commands so each says to run from `midterms/lwg0320/`.
- [ ] Update the README scope statement and Week 3 discussion header/thread with the Minesweeper-on-hexes scope change from the earlier Poolshark direction. Use [`WEEK3-SCOPE-UPDATE.md`](../WEEK3-SCOPE-UPDATE.md) as a draft, edit it to match the original Week 3 post, and link the acceptance trace.
- [ ] Complete a 15-minute appointment playtest of a partner's game during the week of November 2, send the partner notes by November 6, and keep an anonymized copy in [`PARTNER-PLAYTEST-NOTES.md`](../PARTNER-PLAYTEST-NOTES.md). This is separate from having someone play your own game and from the later silent reviews.
- [ ] Run the observation-only model and bounded-history model against the same three declared seeds, two trials each, and run both on held-out seeds. Record live outcomes, failures, limits, illegal moves, latency, tokens, dated cost, model/config, and final game commit in `EVALUATION.md`.
- [ ] Complete one live model episode with an action trace. The recording-only page mode is `/?recording=model`; the regular game page continues to show the deterministic Game playing agent.
- [ ] Have another person play the build while you watch without helping. Fill [`PLAYTEST-NOTES.md`](../PLAYTEST-NOTES.md) anonymously, or explain in `EVALUATION.md` why it was impossible and what a playtest would check.
- [ ] Make and link a three-to-five-minute recording showing the model agent playing without manual move selection and stating its limits. Use [`RECORDING-CHECKLIST.md`](../RECORDING-CHECKLIST.md).
- [ ] Add the recording link to the README and course PR description.
- [ ] Invoke `hex-minesweeper-player` by exact name in two distinct Codex sessions, use it on public observation/action data, and add both links and brief usage details to [`skill-usage.md`](skill-usage.md). Two turns in one chat or automatic file loading do not count as two sessions.
- [ ] Complete the live provider trials. The brief says course Google Cloud credits on Vertex AI count as provider access; ChatGPT Plus does not cover API usage. The current adapter uses OpenAI Responses API, so if you choose Vertex AI, update the adapter/config before running the live suite.
- [ ] If no live provider can be accessed, contact the instructor now to agree on any reduced suite in advance. Mocked responses verify the application but do not count as live model trials.
- [x] A separate read-only Codex subagent reviewed the current diff and confirmed the fixes; the scope, findings, and limits are in [`REVIEW.md`](REVIEW.md).
- [ ] The course's Codex evidence specifically asks for a separate CLI/cloud review session. If required, run that fresh read-only session with no instruction to approve, link it in the PR, and record the real link in [`agent/config.json`](config.json); do not treat this subagent report as a CLI/cloud session link.
- [ ] Rewrite the full one-page team log in the student's own voice, including each role's access, recommendation, decision, and evidence location. Use the real human playtest notes; do not submit the agent-written scaffold as the final log.
- [ ] After pushing the submission branch and opening the course PR, add the implementation-session link and links to `AGENTS.md`, the skill-use evidence, review, and team log to the PR description. A paste-ready block is in [`pr-body-template.md`](pr-body-template.md). The current Codex task has an in-app locator in `AGENT-TEAM.md`; a PR has not been linked here.
- [x] Commit and push the prepared project to the personal Hexsweeper repository. The course hand-in still must be copied to the course repository; a personal-repository URL is not a submission.
- [ ] After assignments arrive on November 9, complete the three silent peer reviews in [`SILENT-PEER-REVIEWS.md`](../SILENT-PEER-REVIEWS.md) before class November 16. This is after the November 7 PR deadline.
