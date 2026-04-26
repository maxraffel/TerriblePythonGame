"""Per-frame collision handling and level-up option building (thin Game orchestration)."""
import random

import pygame

from .settings import (
    ENEMY_BULLET_DAMAGE,
    KNOCKBACK_BASE,
    MAX_WEAPON_SLOTS,
    PLAYER_ENEMY_TOUCH_DAMAGE,
    TELEPORT_COOLDOWN_MS,
    TELEPORT_NUDGE,
)
from .weapons import (
    CalculatorLaser,
    CoffeeBomb,
    MarkerSpray,
    NotebookMissiles,
    PencilWand,
    RulerWave,
    StaplerBurst,
    StickyNotes,
    TextbookOrbit,
    USBBoomerang,
)

vec = pygame.math.Vector2

ALL_WEAPONS = (
    PencilWand,
    CoffeeBomb,
    TextbookOrbit,
    MarkerSpray,
    StaplerBurst,
    CalculatorLaser,
    USBBoomerang,
    StickyNotes,
    NotebookMissiles,
    RulerWave,
)


def handle_collisions(game):
    _projectiles_vs_enemies(game)
    _gems_vs_player(game)
    _coins_vs_player(game)
    _items_vs_player(game)
    _enemies_vs_player(game)
    _enemy_projectiles_vs_player(game)
    _teleports(game)


def _projectiles_vs_enemies(game):
    for proj in game.projectiles:
        hits = pygame.sprite.spritecollide(proj, game.enemies, False)
        for enemy in hits:
            if enemy in proj.hit_enemies:
                continue
            proj.hit_enemies.add(enemy)
            _maybe_knockback_enemy(enemy, proj.vel, KNOCKBACK_BASE * 0.9)
            killed = enemy.take_damage(proj.damage)
            if killed:
                game.player.score += 50
            proj.pierce_count -= 1
            if proj.pierce_count <= 0:
                proj.kill()
                break


def _maybe_knockback_enemy(enemy, vel, magnitude):
    if hasattr(enemy, "apply_knockback") and vel.length() > 0.25:
        enemy.apply_knockback(vel, magnitude=magnitude)


def _gems_vs_player(game):
    gem_hits = pygame.sprite.spritecollide(game.player, game.gems, True)
    for gem in gem_hits:
        game.player.gain_xp(gem.value)


def _coins_vs_player(game):
    coin_hits = pygame.sprite.spritecollide(game.player, game.coins, True)
    for _ in coin_hits:
        game.session_coins += 1


def _items_vs_player(game):
    item_hits = pygame.sprite.spritecollide(game.player, game.items, True)
    for item in item_hits:
        _resolve_item_pickup(game, item)


def _resolve_item_pickup(game, item):
    player = game.player
    if not hasattr(item, "type"):
        player.score += 10
        player.energy = min(player.max_energy, player.energy + 20)
        return

    if item.type == "chest":
        player.score += 200
        upgradable = [w for w in player.weapons if w.level < w.max_level]
        if upgradable:
            w = random.choice(upgradable)
            w.level += 1
            print(f"Chest upgraded {w.name} to level {w.level}!")
        return

    player.score += 50
    player.powerup = item.type
    player.powerup_time = pygame.time.get_ticks() + 10000


def _enemies_vs_player(game):
    player = game.player
    enemy_hits = pygame.sprite.spritecollide(player, game.enemies, False)
    if not enemy_hits:
        return
    for enemy in enemy_hits:
        if player.powerup == "shield":
            enemy.take_damage(999)
            player.score += 50
        else:
            player.energy -= PLAYER_ENEMY_TOUCH_DAMAGE
            enemy.kill()


def _enemy_projectiles_vs_player(game):
    player = game.player
    hits = pygame.sprite.spritecollide(player, game.enemy_projectiles, True)
    if not hits or player.powerup == "shield":
        return
    for _ in hits:
        player.energy -= ENEMY_BULLET_DAMAGE


def _teleports(game):
    player = game.player
    now = pygame.time.get_ticks()
    if now < player.teleport_lock_until:
        return
    hits = pygame.sprite.spritecollide(player, game.teleporters, False)
    if not hits:
        return
    pad = hits[0]
    to = pad.dest
    nudge = to - pad.pos
    if nudge.length() < 0.01:
        nudge = vec(1.0, 0.0)
    else:
        nudge = nudge.normalize() * TELEPORT_NUDGE
    player.pos = to + nudge
    player.rect.center = (int(player.pos.x), int(player.pos.y))
    player.teleport_lock_until = now + TELEPORT_COOLDOWN_MS


def collect_upgrade_options(game):
    player = game.player
    owned = {type(w): w for w in player.weapons}
    out = []

    for w_class in ALL_WEAPONS:
        if w_class not in owned and len(player.weapons) < MAX_WEAPON_SLOTS:
            out.append(
                {
                    "title": f"New: {w_class.name}",
                    "desc": w_class.description,
                    "action": lambda wc=w_class: player.weapons.append(wc(game)),
                }
            )

    for w in player.weapons:
        if w.level < w.max_level:
            out.append(
                {
                    "title": f"Upgrade: {w.name}",
                    "desc": f"Increase {w.name} to Level {w.level + 1}",
                    "action": lambda w=w: setattr(w, "level", w.level + 1),
                }
            )

    out.extend(_passive_upgrade_options(player))
    return out


def _passive_upgrade_options(player):
    def caffeine():
        player.passive_stats.update(
            {"firerate_mult": player.passive_stats["firerate_mult"] * 0.8}
        )

    def all_nighter():
        player.passive_stats.update(
            {"speed_mult": player.passive_stats["speed_mult"] * 1.2}
        )

    return [
        {
            "title": "Caffeine Rush",
            "desc": "+20% Fire Rate",
            "action": caffeine,
        },
        {
            "title": "All-Nighter",
            "desc": "+20% Move Speed",
            "action": all_nighter,
        },
    ]


def finalize_upgrade_choices(possible_upgrades, rng=None):
    rng = rng or random
    if len(possible_upgrades) > 3:
        chosen = rng.sample(possible_upgrades, 3)
    else:
        chosen = possible_upgrades
    return [(opt["title"], opt["desc"], opt["action"]) for opt in chosen]
