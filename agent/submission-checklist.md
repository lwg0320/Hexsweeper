# Agent-team evidence checklist

## Prepared artifacts

- [x] Implementation-agent instructions are prepared in [`AGENTS.md`](../AGENTS.md); the current Codex task locator is in [`AGENT-TEAM.md`](../AGENT-TEAM.md) and [`agent/config.json`](config.json).
- [x] Reusable skill is present at [`hex-minesweeper-player`](../hex_minesweeper/skills/hex-minesweeper-player/SKILL.md).
- [x] A fresh independent-review report and its read-only prompt are present in [`REVIEW.md`](REVIEW.md) and [`independent-review.md`](independent-review.md); the report covers the current Claude integration and records the reviewer's findings and author dispositions.
- [x] A factual team-log scaffold lists roles, access, recommendations, decisions, and evidence in [`AGENT-TEAM.md`](../AGENT-TEAM.md).

## Evidence still needed for a complete submission

- [ ] Place the complete project in the course repository at `midterms/lwg0320/`; the current checkout is the personal `lwg0320/Hexsweeper` repository at its root.
- [ ] Include the prepared workflow as `.github/workflows/midterm-lwg0320.yml` in the course PR. It is scoped to `midterms/lwg0320/**`; do not include another unrelated workflow change in that PR.
- [ ] Verify setup, play, tests, and evaluation from a fresh clone of the final course PR head using the README commands. The new brief says staff read the graded commit from the PR timeline; there is no need to name a commit or create a tag.
- [x] README commands state that the course-repository working directory is `midterms/lwg0320/` for setup, play, tests, and evaluation; the development checkout uses its root.
- [x] README scope statement identifies the Minesweeper-on-hexes scope change from the earlier Poolshark direction and names the first cuts.
- [x] Local verification on 2026-11-06: 45 unit tests passed on Python 3.8.0; browser JavaScript syntax and whitespace checks passed; the status endpoint is tested with both configured and blank Claude keys. This is not a GitHub Actions result.
- [x] The declared and held-out deterministic baseline suite was rerun locally; 10 complete traces are in [`evaluation/baseline-working-tree-2026-11-06.jsonl`](../evaluation/baseline-working-tree-2026-11-06.jsonl). The trace records a dirty tree and must be regenerated on the final course PR commit.
- [ ] Post the scope change in the original Week 3 discussion thread. Edit [`WEEK3-SCOPE-UPDATE.md`](../WEEK3-SCOPE-UPDATE.md) to match the original post and link the acceptance trace; record the real thread link/date.
- [x] The revised human-playtest item accepts any person playing your build; an anonymous friend played all three sizes while you watched without helping. The notes in [`PLAYTEST-NOTES.md`](../PLAYTEST-NOTES.md) cover what they tried, where they hesitated, their difficulty impression, and a possible change. A partner playing someone else's build is not needed to satisfy this item.
- [x] Run the observation-only model and bounded-history model against the same three declared seeds, two trials each, and run both on held-out seeds. Live outcomes, failures, limits, illegal moves, latency, tokens, dated cost, model/config, and trace links are in [`EVALUATION.md`](../EVALUATION.md). The trace is from a dirty local tree and must be regenerated on the final course PR commit.
- [x] The live model comparison contains individual Claude API episodes and action traces. The no-API gameplay recording remains separate and does not substitute for model-comparison evidence.
- [ ] Make and link a three-to-five-minute recording showing the deterministic Game playing agent playing without manual move selection and stating its limits. Use [`RECORDING-CHECKLIST.md`](../RECORDING-CHECKLIST.md).
- [ ] Add the recording link to the README and course PR description.
- [x] Invoke `hex-minesweeper-player` by exact name in two distinct Codex sessions, use it on public observation/action data, and add both links and brief usage details to [`skill-usage.md`](skill-usage.md). Two turns in one chat or automatic file loading do not count as two sessions.
- [x] Complete the declared and held-out live provider trials using the Anthropic Claude API adapter. Mocked responses verify the application but do not count as live model trials; the paired live traces are linked in [`EVALUATION.md`](../EVALUATION.md).
- [x] Not applicable: live Claude API access was available and the full declared and held-out comparison was completed; no reduced-suite exception is needed.
- [x] Commission a fresh independent read-only review of the current Claude API, key-status UI, retry/fallback handling, information boundaries, limits, and documentation.
- [x] Capture the reviewer's actual session link and findings in [`REVIEW.md`](REVIEW.md) and [`agent/config.json`](config.json). The reviewer did not write the code and received no instruction to approve it.
- [ ] Rewrite the full one-page team log in the student's own voice, including each role's access, recommendation, decision, and evidence location. Use the real human playtest notes; do not submit the agent-written scaffold as the final log.
- [ ] After pushing the submission branch and opening the course PR, add the implementation-session link and links to `AGENTS.md`, the skill-use evidence, review, and team log to the PR description. A paste-ready block is in [`pr-body-template.md`](pr-body-template.md). The current Codex task has an in-app locator in `AGENT-TEAM.md`; a PR has not been linked here.
- [x] The personal Hexsweeper repository is separate from the course hand-in. Keep subsequent changes local unless the user explicitly requests another push; a personal-repository URL is not a submission.
- [ ] After assignments arrive on November 9, complete the three silent peer reviews in [`SILENT-PEER-REVIEWS.md`](../SILENT-PEER-REVIEWS.md) before class November 16. This is after the November 7 PR deadline.
