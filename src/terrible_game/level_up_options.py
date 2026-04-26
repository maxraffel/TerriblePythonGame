"""Level-up upgrade picker options (extracted from Game for lower CC)."""

import random

from .settings import MAX_WEAPON_SLOTS
from .weapons import ALL_WEAPON_CLASSES


def build_upgrade_options(game):
    owned = {type(w): w for w in game.player.weapons}
    possible = []

    for w_class in ALL_WEAPON_CLASSES:
        if w_class in owned:
            continue
        if len(game.player.weapons) >= MAX_WEAPON_SLOTS:
            continue
        possible.append(
            {
                "title": f"New: {w_class.name}",
                "desc": w_class.description,
                "action": lambda wc=w_class: game.player.weapons.append(wc(game)),
            }
        )

    for w in game.player.weapons:
        if w.level >= w.max_level:
            continue
        possible.append(
            {
                "title": f"Upgrade: {w.name}",
                "desc": f"Increase {w.name} to Level {w.level + 1}",
                "action": lambda w=w: setattr(w, "level", w.level + 1),
            }
        )

    possible.extend(
        [
            {
                "title": "Caffeine Rush",
                "desc": "+20% Fire Rate",
                "action": lambda: game.player.passive_stats.update(
                    {
                        "firerate_mult": game.player.passive_stats["firerate_mult"]
                        * 0.8
                    }
                ),
            },
            {
                "title": "All-Nighter",
                "desc": "+20% Move Speed",
                "action": lambda: game.player.passive_stats.update(
                    {
                        "speed_mult": game.player.passive_stats["speed_mult"] * 1.2
                    }
                ),
            },
        ]
    )

    if len(possible) > 3:
        chosen = random.sample(possible, 3)
    else:
        chosen = possible

    return [(opt["title"], opt["desc"], opt["action"]) for opt in chosen]
