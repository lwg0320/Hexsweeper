# Independent review of current implementation

**Review date:** 2026-11-06
**Reviewer session:** [Independent Hexsweeper review](codex://threads/01a1b302-e7fb-7be2-aed4-de5184f40cdb)
**Reviewer access:** Separate Codex task with the current working tree. It was instructed to read only, make no edits, avoid `.env` and secrets, and make no network or model calls.
**Prompt:** [independent-review.md](independent-review.md)

The reviewer covered the current Claude integration, public observation/action boundaries, rules and terminal outcomes, retry/fallback and episode limits, prompt cache/token accounting, key-status UI, tests, documentation, and course workflow. It did not test a live provider request. The reported 44-test result was from before the final coordinate-validation test was added.

## Reviewer findings and author disposition

1. **[P1] API-key bearer authentication.** The reviewer believed `Authorization: Bearer` was invalid for a static Anthropic API key. I did not change this: Anthropic's current [authentication documentation](https://platform.claude.com/docs/en/manage-claude/authentication) explicitly supports API keys in that header, and the subsequent live comparison completed authenticated Claude requests. The reviewer's claim does not apply to the API version used here.
2. **[P2] Malformed coordinates could bypass retry/fallback.** Confirmed. A float coordinate can compare equal to an integer in Python dictionaries, pass list membership, and then fail `Game.step` validation. I fixed the runner to validate exact action keys and types before legality comparison and added a regression test proving the invalid response is retried before applying a legal move.
3. **[P2] Tool definition not included in cache.** I did not change this implementation. Anthropic's [prompt caching documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) defines prefix order as `tools` then `system` then `messages`; the breakpoint on the system block therefore covers the preceding tool definition. The live trace also records cache-write and cache-read tokens. The report now says cache activity was observed but does not claim savings without a cache-disabled control.
4. **[P3] API-cost notice omitted a retry.** Confirmed and fixed. The consent/status copy now says one request is usual, an invalid selection can trigger one retry, and the total episode budget is 80 calls.
5. **[P3] Source map cited nonexistent `neighbor_mines`.** Confirmed and fixed. The rule row now points to the `_numbers` calculation in `Game._place_mines_safely`.

## Checks with no finding

The reviewer found no direct preterminal seed or mine leak. The deterministic solver and Claude agent receive public observations and legal actions; bounded history contains public actions/results only. It found the course workflow correctly scoped. The live evaluation recorded 30 paired episodes afterward; full results and the network-sandbox preflight failure are in [EVALUATION.md](../EVALUATION.md) and its linked traces.

After addressing the confirmed findings, the local suite passed 45 tests; JavaScript syntax and `git diff --check` passed. This is an independent read-only review of the current integration plus author follow-up. It is not GitHub Actions evidence, and the review itself did not make API calls.
