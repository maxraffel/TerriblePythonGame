"""Highscore, time, coins, and meta-upgrade persistence (decoupled from Game)."""

import json
import os


def default_progress_state():
    return {
        "highscore": 0,
        "hightime": 0,
        "global_coins": 0,
        "global_upgrades": {"damage": 0, "speed": 0, "energy": 0},
    }


def load_progress(game_dir: str) -> dict:
    state = default_progress_state()
    path = os.path.join(game_dir, "highscore.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        state["highscore"] = int(data.get("score", 0))
        state["hightime"] = int(data.get("time", 0))
        state["global_coins"] = int(data.get("global_coins", 0))
        loaded = data.get("global_upgrades") or {}
        for k in state["global_upgrades"]:
            if k in loaded:
                state["global_upgrades"][k] = int(loaded[k])
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return state


def save_progress(
    game_dir: str,
    *,
    highscore: int,
    hightime: int,
    global_coins: int,
    global_upgrades: dict,
) -> None:
    path = os.path.join(game_dir, "highscore.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "score": highscore,
                "time": hightime,
                "global_coins": global_coins,
                "global_upgrades": global_upgrades,
            },
            f,
        )
