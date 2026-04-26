"""Small helpers for couch co-op — keeps `game.py` slimmer (Kowalski: high susceptibility)."""
from pygame.math import Vector2 as _Vec


def all_players(game):
    return getattr(game, "all_players", [game.player])


def camera_center(game):
    ps = all_players(game)
    if len(ps) == 1:
        return _Vec(ps[0].pos)
    acc = _Vec(0, 0)
    for p in ps:
        acc += p.pos
    return acc / len(ps)


def nearest_player(game, from_pos):
    ps = all_players(game)
    best = ps[0]
    best_d = from_pos.distance_to(best.pos)
    for p in ps[1:]:
        d = from_pos.distance_to(p.pos)
        if d < best_d:
            best_d = d
            best = p
    return best


def combined_score(game):
    return sum(p.score for p in all_players(game))
