# Recording verification and hand-in

The recorded file is [`hexsweeper-recording.mp4`](hexsweeper-recording.mp4). AVFoundation reports a duration of 292.135 seconds (4:52), one video track, and one audio track. The compressed MP4 is about 44.3 MB; `vid.mov` is the 256 MB original and is ignored by Git.

Sampled frames show the game at several sizes, an automatically running deterministic **Game playing agent**, and a mine-reveal terminal loss. The video later shows the Claude API agent running automatically as well. The mine-hit ending is visible in the game UI.

The owner confirmed on 2026-11-06 that the narration explicitly states the deterministic agent's limits: it sees only public board information, it can still need to guess, and each episode has an 80-decision limit. I verified the picture and duration; I did not independently transcribe the audio.

For the course PR, include `hexsweeper-recording.mp4` in `midterms/lwg0320/`, link it from the README, and replace the branch placeholder in [`agent/pr-body-template.md`](agent/pr-body-template.md) with the actual GitHub file URL. The course repository is public; confirm the link opens without a personal-account permission prompt so the instructor, TAs, and assigned peer reviewers can view it.
