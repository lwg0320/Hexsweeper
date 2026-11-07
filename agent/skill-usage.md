# Reusable skill invocation evidence

Skill: [`hex-minesweeper-player`](../hex_minesweeper/skills/hex-minesweeper-player/SKILL.md)

The model adapter loads this prompt for each model decision. That proves the project integration, but it does not by itself prove the course's requirement that the skill be invoked by name in two separate assistant sessions.

The rows below record two distinct Codex sessions. Each invoked `hex-minesweeper-player` by exact name on a real public observation/legal-action pair and reports its returned action. Do not count repeated turns in one chat or infer invocation from the model adapter loading the file.

| Session | Link | What the skill was used to do |
|---|---|---|
| 1 — 2026-11-06 | [Codex skill-use session 1](codex://threads/01a1b302-d130-7351-8244-01c07416658b) | Invoked `hex-minesweeper-player` by name on a public radius-3 observation with one revealed center clue (2), 6 public mines, and the supplied legal actions. Returned legal reveal `(-3, 0)` as an uncertain guess, estimating 4 mines among 30 non-neighbor cells. |
| 2 — 2026-11-06 | [Codex skill-use session 2](codex://threads/01a1b302-db1f-7491-b004-b051d09db984) | Invoked `hex-minesweeper-player` by name on the same public observation/action pair. Returned legal reveal `(-3, 0)` as a guess because the only clue constrained its six adjacent cells. |
