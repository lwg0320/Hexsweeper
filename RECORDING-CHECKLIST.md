# Recording checklist

Before recording, start the server with the live model key configured and open `http://127.0.0.1:8000/?recording=model`. That URL exposes a recording-only **Start live model playback** control; the normal page keeps model controls hidden. The moves happen automatically after you click it. Do not manually choose or submit them. Each move makes a provider call and may incur cost.

- Keep the recording between three and five minutes.
- Show the game, explain the hex clues and selected map size, and show the model agent choosing and submitting actions.
- Identify which agent is playing. Do not present the deterministic baseline as the model-driven player.
- State the run's step, model-call, and timeout limits, and explain any failure or incomplete outcome honestly.
- Avoid showing API keys, private credentials, hidden answer data, or a playtester's identity.
- Add a link viewable by the instructor, TAs, and assigned peer reviewers to both `README.md` and the PR description.
