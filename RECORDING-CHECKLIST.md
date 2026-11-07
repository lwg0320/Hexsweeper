# Recording checklist

This recording shows the website's deterministic **Game playing agent**. It does not require a live model API. From the project root, start the server with `python3 -m hex_minesweeper.server`, open `http://127.0.0.1:8000`, select a map size, and choose **Run game playing agent**. Let the agent make every move automatically; do not manually choose or submit moves. The main page also offers a separate Claude API agent; do not use or describe that player as the deterministic agent in this video.

- Keep the recording between three and five minutes.
- Show the game, explain the hex clues and selected map size, and show the Game playing agent choosing and submitting actions.
- Identify it accurately as the deterministic constraint-solving agent. Do not call it an LLM or model-driven player.
- State its limits: it sees only the public board, can guess when the clues do not force a move, and runs under the game's 80-action episode limit. Explain any failure or incomplete outcome honestly.
- Avoid showing hidden answer data or a playtester's identity.
- Add a link viewable by the instructor, TAs, and assigned peer reviewers to both `README.md` and the PR description.
