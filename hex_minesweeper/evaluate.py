"""Run paired baseline and live-model episodes on the same seeded openings."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
import time
from typing import Any

from .model_agent import ModelAgent, pricing_metadata
from .runner import EpisodeRunner

OPENING = (0, 0)


def play(policy: str, seed: int | str) -> dict[str, Any]:
    runner = EpisodeRunner(seed, fixed_opening=OPENING)
    model = ModelAgent() if policy == "model" else None
    started = time.monotonic()
    while not runner.outcome()["terminal"]:
        if policy == "baseline":
            runner.baseline_step()
        else:
            runner.model_step(model)
    return {
        "policy": policy,
        "seed": seed,
        "shared_opening": {"type": "reveal", "q": OPENING[0], "r": OPENING[1]},
        "result": runner.outcome(),
        "metrics": runner.metrics(),
        "wall_time_ms": int((time.monotonic() - started) * 1000),
        "trace": runner.trace,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="1401,1402,1403",
                        help="comma-separated declared board seeds")
    parser.add_argument("--trials", type=int, default=2,
                        help="repeat each paired seed this many times")
    parser.add_argument("--players", default="baseline,model",
                        help="comma-separated players: baseline,model")
    args = parser.parse_args(argv)
    if args.trials < 1:
        parser.error("--trials must be at least 1")
    seeds = [item.strip() for item in args.seeds.split(",") if item.strip()]
    players = [item.strip() for item in args.players.split(",") if item.strip()]
    if not seeds:
        parser.error("--seeds must contain at least one seed")
    if not players or any(player not in ("baseline", "model") for player in players):
        parser.error("--players must contain baseline and/or model")
    print(json.dumps({
        "kind": "evaluation_header",
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "seeds": seeds,
        "trials_per_seed": args.trials,
        "fixed_opening": {"q": OPENING[0], "r": OPENING[1]},
        "max_steps": 80,
        "max_model_calls": 80,
        "model_timeout_seconds": 20,
        "pricing": pricing_metadata(),
    }))
    for seed in seeds:
        for trial in range(1, args.trials + 1):
            # Baseline and model start from the same fixed board and opening.
            for policy in players:
                try:
                    result = play(policy, seed)
                except Exception as error:
                    result = {
                        "policy": policy, "seed": seed, "trial": trial,
                        "failure": str(error),
                    }
                result["trial"] = trial
                print(json.dumps(result, separators=(",", ":")))
                sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
