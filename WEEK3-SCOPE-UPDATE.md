# Week 3 scope update

**Status:** posted as a reply to my original Week 3 entry on November 6, 2026.

> **AI-use disclosure:** I used Codex to build the game and help draft this update; I reviewed the facts and wording.
>
> **Scope update (November 7):** I am changing my project from Atari Pool Shark to Hexsweeper, a small Minesweeper adaptation on a hex grid, built from scratch. I kept the familiar reveal-and-flag loop and chose six neighbors, three board sizes, a safe first reveal, and clear win/loss endings. The first reveal can still show only a clue. I left out timers, chording, question-mark marks, power-ups, and high scores. I chose hexes to make the adaptation distinct while keeping the deduction game small enough to finish and test. If I need to cut scope further, I will remove the small and large presets and keep the medium-board loop and player interface.
>
> **Evidence:** The [rule/source map](https://github.com/lwg0320/Hexsweeper/blob/main/RULE_SOURCE_MAP.md) explains which rules follow the Minesweeper reference and which are my design choices. A complete [baseline acceptance trace](https://github.com/lwg0320/Hexsweeper/blob/main/evaluation/baseline-smoke-2026-10-26.jsonl) records one episode. I did not reuse Pool Shark code, ROM data, or assets.

- Week 3 thread and reply: https://courseworks2.columbia.edu/courses/258228/discussion_topics/1669984?entry_id=5282356
- Date posted: November 6, 2026
