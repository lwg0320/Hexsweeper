# Coding-agent instructions

## Project goal

Maintain Hexsweeper as a small, complete hex Minesweeper game with a human player, a deterministic game-playing agent, and a model player behind the same observation/action boundary. Do not add unrelated mechanics.

## Rules and information boundary

- Treat `hex_minesweeper/game.py` as the authoritative rules implementation and `RULE_SOURCE_MAP.md` as the source/choice record.
- The runner owns the authoritative game. Players may use only public observations and legal actions; never expose the seed or hidden mine locations before the game ends.
- Preserve explicit illegal-action handling, episode limits, model-call limits, timeouts, and terminal reasons.
- Keep source claims, assumptions, observed behavior, and project choices distinct in documentation.

## Player instructions

The reusable player prompt is named `hex-minesweeper-player` and lives at `hex_minesweeper/skills/hex-minesweeper-player/SKILL.md`. The model adapter loads it for model decisions. The evaluator supports observation-only and bounded-history model variants; history contains only up to eight prior public actions/results. For course evidence, invoke the named skill in two separate assistant sessions and record both real session links in `agent/skill-usage.md`; do not infer invocation from the file merely existing.

## Website

The ordinary website exposes the human controls and the deterministic **Game playing agent**. Model playback is available only through the explicit `/?recording=model` mode, where the visitor must click Start; do not expose model controls on the ordinary page.

## Checks and evidence

- Run deterministic checks with `python3 -m unittest discover -s tests -v` when asked to verify changes.
- Check browser JavaScript syntax with `node --check hex_minesweeper/static/app.js` after editing it.
- Keep implementation, skill-use, review, and student-authored evidence references in `AGENT-TEAM.md` and `agent/submission-checklist.md` accurate. Never invent a session, review finding, playtest, or student reflection.
- The implementation task is recorded in `AGENT-TEAM.md` and `agent/config.json`. Link it from the actual submission PR when one exists.
- The course hand-in target is `midterms/lwg0320/` with the single workflow `.github/workflows/midterm-lwg0320.yml`; do not include this standalone repository's general workflow in the course PR.
