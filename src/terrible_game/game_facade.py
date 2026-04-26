"""
Run-loop helpers for Game in one module (single outbound edge from game for Kowalski).

Combines teleport placement, sprite culling, world drawing, pygame events, and
run finalization so the orchestrator does not fan out to many small packages.
"""

import math

import pygame
from pygame.math import Vector2

from .persistence import save_progress
from .settings import HEIGHT, TELEPORT_PAIR_SPACING, WIDTH
from .sprites import TeleportPad

vec = Vector2


def place_default_teleport_pairs(game):
    """
    Three links in different map regions. Within each link, pads are
    TELEPORT_PAIR_SPACING apart (horizontal, vertical, or 45°).
    """
    cx, cy = WIDTH // 2, HEIGHT // 2
    s = float(TELEPORT_PAIR_SPACING)
    o = 1.0 / math.sqrt(2.0)
    diag = vec(-s * o, -s * o)

    a0 = vec(cx - 920, cy - 560)
    a1 = vec(cx + 880, cy + 620)
    a2 = vec(cx - 420, cy + 1020)
    pairs = [
        (a0, a0 + vec(s, 0)),
        (a1, a1 + vec(0, s)),
        (a2, a2 + diag),
    ]
    for a, b in pairs:
        pa = TeleportPad(a.x, a.y, b)
        pb = TeleportPad(b.x, b.y, a)
        for p in (pa, pb):
            game.teleporters.add(p)
            game.all_sprites.add(p)


def cull_distant_sprites(game, max_distance: float = 2500.0) -> None:
    for sprite in game.all_sprites:
        if not hasattr(sprite, "pos"):
            continue
        if getattr(sprite, "world_static", False):
            continue
        if game.player.pos.distance_to(sprite.pos) > max_distance:
            sprite.kill()


def draw_floor_grid(screen, cam_x, cam_y):
    tile_size = 100
    start_x = int(cam_x // tile_size) * tile_size
    start_y = int(cam_y // tile_size) * tile_size
    color1 = (40, 40, 50)
    color2 = (35, 35, 45)
    for x in range(int(start_x), int(start_x + WIDTH + tile_size), tile_size):
        for y in range(int(start_y), int(start_y + HEIGHT + tile_size), tile_size):
            screen_x = x - cam_x
            screen_y = y - cam_y
            is_even = ((x // tile_size) + (y // tile_size)) % 2 == 0
            color = color1 if is_even else color2
            pygame.draw.rect(screen, color, (screen_x, screen_y, tile_size, tile_size))


def blit_sprites_camera(screen, sprites, cam_x, cam_y):
    for sprite in sprites:
        screen_pos = (sprite.rect.x - cam_x, sprite.rect.y - cam_y)
        screen.blit(sprite.image, screen_pos)


def draw_playfield(game):
    current_zone = game.spawn_manager.get_current_zone()
    game.screen.fill(current_zone["bg_color"])
    cam_x = game.player.pos.x - WIDTH / 2
    cam_y = game.player.pos.y - HEIGHT / 2
    draw_floor_grid(game.screen, cam_x, cam_y)
    blit_sprites_camera(game.screen, game.all_sprites, cam_x, cam_y)


def pump_quit_and_level_up_keys(game) -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if game.playing:
                game.playing = False
            game.running = False
            continue
        if event.type != pygame.KEYDOWN or not game.is_leveling_up:
            continue
        if event.key == pygame.K_1:
            game.select_upgrade(0)
        elif event.key == pygame.K_2:
            game.select_upgrade(1)
        elif event.key == pygame.K_3:
            game.select_upgrade(2)


def finalize_run(game) -> None:
    time_survived = (pygame.time.get_ticks() - game.start_time) // 1000
    if game.player.score > game.highscore:
        game.highscore = game.player.score
    if time_survived > game.hightime:
        game.hightime = time_survived
    game.coins_earned_last_run = game.session_coins
    game.global_coins += game.session_coins
    save_progress(
        game.dir,
        highscore=game.highscore,
        hightime=game.hightime,
        global_coins=game.global_coins,
        global_upgrades=game.global_upgrades,
    )
