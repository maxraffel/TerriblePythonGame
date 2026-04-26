"""Projectile, pickup, and player collision handling (extracted from Game for lower CC)."""

import random

import pygame
from pygame.math import Vector2

from .settings import (
    ENEMY_BULLET_DAMAGE,
    KNOCKBACK_BASE,
    PLAYER_ENEMY_TOUCH_DAMAGE,
    TELEPORT_COOLDOWN_MS,
    TELEPORT_NUDGE,
)

vec = Vector2


def _projectile_enemy_hits(game):
    for proj in game.projectiles:
        hits = pygame.sprite.spritecollide(proj, game.enemies, False)
        for enemy in hits:
            if enemy in proj.hit_enemies:
                continue
            proj.hit_enemies.add(enemy)
            if hasattr(enemy, "apply_knockback") and proj.vel.length() > 0.25:
                enemy.apply_knockback(proj.vel, magnitude=KNOCKBACK_BASE * 0.9)
            killed = enemy.take_damage(proj.damage)
            if killed:
                game.player.score += 50
            proj.pierce_count -= 1
            if proj.pierce_count <= 0:
                proj.kill()
                break


def _gem_pickups(game):
    gem_hits = pygame.sprite.spritecollide(game.player, game.gems, True)
    for gem in gem_hits:
        game.player.gain_xp(gem.value)


def _coin_pickups(game):
    coin_hits = pygame.sprite.spritecollide(game.player, game.coins, True)
    for _ in coin_hits:
        game.session_coins += 1


def _item_pickups(game):
    item_hits = pygame.sprite.spritecollide(game.player, game.items, True)
    for item in item_hits:
        if not hasattr(item, "type"):
            game.player.score += 10
            game.player.energy = min(
                game.player.max_energy, game.player.energy + 20
            )
            continue
        if item.type == "chest":
            game.player.score += 200
            upgradable = [w for w in game.player.weapons if w.level < w.max_level]
            if upgradable:
                w = random.choice(upgradable)
                w.level += 1
                print(f"Chest upgraded {w.name} to level {w.level}!")
            continue
        game.player.score += 50
        game.player.powerup = item.type
        game.player.powerup_time = pygame.time.get_ticks() + 10000


def _player_enemy_touch(game):
    enemy_hits = pygame.sprite.spritecollide(game.player, game.enemies, False)
    if not enemy_hits:
        return
    for enemy in enemy_hits:
        if game.player.powerup == "shield":
            enemy.take_damage(999)
            game.player.score += 50
        else:
            game.player.energy -= PLAYER_ENEMY_TOUCH_DAMAGE
            enemy.kill()


def _player_enemy_bullets(game):
    hits = pygame.sprite.spritecollide(game.player, game.enemy_projectiles, True)
    if not hits:
        return
    if game.player.powerup == "shield":
        return
    for _ in hits:
        game.player.energy -= ENEMY_BULLET_DAMAGE


def _apply_teleports(game):
    now = pygame.time.get_ticks()
    if now < game.player.teleport_lock_until:
        return
    hits = pygame.sprite.spritecollide(game.player, game.teleporters, False)
    if not hits:
        return
    pad = hits[0]
    to = pad.dest
    nudge = to - pad.pos
    if nudge.length() < 0.01:
        nudge = vec(1.0, 0.0)
    else:
        nudge = nudge.normalize() * TELEPORT_NUDGE
    game.player.pos = to + nudge
    game.player.rect.center = (int(game.player.pos.x), int(game.player.pos.y))
    game.player.teleport_lock_until = now + TELEPORT_COOLDOWN_MS


def handle_collisions(game):
    _projectile_enemy_hits(game)
    _gem_pickups(game)
    _coin_pickups(game)
    _item_pickups(game)
    _player_enemy_touch(game)
    _player_enemy_bullets(game)
    _apply_teleports(game)
