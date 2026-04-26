"""Title, character select, and shop loops (split from UI for lower cyclomatic complexity)."""

import pygame

from .characters import CHARACTERS
from .settings import (
    BGCOLOR,
    FPS,
    HEIGHT,
    SHOP_BASE_COST,
    SHOP_MAX_LEVEL,
    SHOP_UPGRADES,
    WHITE,
    WIDTH,
    YELLOW,
)


def _char_key_to_index(key):
    mapping = (pygame.K_1, pygame.K_2, pygame.K_3)
    for i, k in enumerate(mapping):
        if key == k:
            return i
    return None


def _draw_character_cards(ui, start_x, y, card_w, card_h, gap):
    for i, ch in enumerate(CHARACTERS):
        wcls = ch["weapon_class"]
        col = getattr(wcls, "ui_color", (120, 120, 130))
        x = start_x + i * (card_w + gap)
        rect = pygame.Rect(x, y, card_w, card_h)
        sc = ui.game.screen
        pygame.draw.rect(sc, (45, 45, 60), rect)
        pygame.draw.rect(sc, col, rect, 3)
        font = pygame.font.Font(ui.font_name, 17)
        sc.blit(font.render(f"[{i + 1}]  {ch['name']}", True, YELLOW), (x + 14, y + 12))
        sc.blit(font.render(wcls.name, True, col), (x + 14, y + 38))
        blurb = pygame.font.Font(ui.font_name, 14)
        for j, line in enumerate(ui._wrap_text(ch["tagline"], blurb, card_w - 28)):
            sc.blit(blurb.render(line, True, (200, 200, 210)), (x + 14, y + 62 + j * 18))


def run_character_select(ui) -> bool:
    """Return True if a character was chosen (1/2/3), False if ESC back to title."""
    card_w, card_h = 340, 120
    gap = 24
    total_w = len(CHARACTERS) * card_w + (len(CHARACTERS) - 1) * gap
    start_x = (WIDTH - total_w) / 2
    y_cards = 180

    while ui.game.running:
        ui.game.screen.fill(BGCOLOR)
        ui.draw_text("CHOOSE YOUR CHARACTER", 44, YELLOW, WIDTH / 2, 50)
        ui.draw_text("Each starts with a different Lv.1 weapon.", 20, WHITE, WIDTH / 2, 100)
        _draw_character_cards(ui, start_x, y_cards, card_w, card_h, gap)
        ui.draw_text("Press 1, 2, or 3 to start  |  ESC: back", 20, WHITE, WIDTH / 2, HEIGHT - 55)
        pygame.display.flip()
        ui.game.clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ui.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                idx = _char_key_to_index(event.key)
                if idx is not None and idx < len(CHARACTERS):
                    ui.game.selected_character_index = idx
                    return True
    return False


def _draw_shop_listing(ui, y_start):
    y = y_start
    for i, (key, title, blurb) in enumerate(SHOP_UPGRADES):
        level = ui.game.global_upgrades.get(key, 0)
        if level >= SHOP_MAX_LEVEL:
            ui.draw_text(
                f"{i + 1}. {title}  —  MAX (Lv {level})",
                24,
                (160, 160, 180),
                WIDTH / 2,
                y,
            )
        else:
            cost = SHOP_BASE_COST * (1 + level)
            ui.draw_text(
                f"{i + 1}. {title}  —  Lv {level}  (next: {cost} coins)",
                24,
                WHITE,
                WIDTH / 2,
                y,
            )
        ui.draw_text(blurb, 16, (180, 180, 200), WIDTH / 2, y + 30)
        y += 88


def run_shop_screen(ui):
    key_map = (pygame.K_1, pygame.K_2, pygame.K_3)
    while ui.game.running:
        ui.game.screen.fill(BGCOLOR)
        ui.draw_text("SHOP", 56, YELLOW, WIDTH / 2, 50)
        ui.draw_text(
            f"Coins: {ui.game.global_coins}",
            28,
            (255, 220, 100),
            WIDTH / 2,
            120,
        )
        _draw_shop_listing(ui, 200)
        ui.draw_text("1, 2, 3: purchase  |  ESC: back to title", 20, WHITE, WIDTH / 2, HEIGHT - 50)
        pygame.display.flip()
        ui.game.clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ui.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                for i, k in enumerate(key_map):
                    if event.key == k and i < len(SHOP_UPGRADES):
                        ukey, _, _ = SHOP_UPGRADES[i]
                        ui._try_buy_upgrade(ukey)
                        break


def run_start_screen(ui):
    while ui.game.running:
        ui.game.screen.fill(BGCOLOR)
        ui.draw_text("MARIO'S ALL-NIGHTER: SURVIVORS", 48, WHITE, WIDTH / 2, HEIGHT / 4)
        ui.draw_text("WASD to move! You will shoot automatically.", 22, WHITE, WIDTH / 2, HEIGHT / 2)
        ui.draw_text(
            "Collect blue gems to level up and gold coins for the shop.",
            22,
            YELLOW,
            WIDTH / 2,
            HEIGHT * 5 / 8,
        )
        ui.draw_text(
            f"Your coins: {ui.game.global_coins}",
            20,
            (255, 220, 100),
            WIDTH / 2,
            HEIGHT * 5 / 8 + 32,
        )
        ui.draw_text(
            "SPACE: Character select  |  S: Shop",
            20,
            WHITE,
            WIDTH / 2,
            HEIGHT * 3 / 4,
        )
        pygame.display.flip()
        ui.game.clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ui.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if run_character_select(ui):
                        return
                if event.key == pygame.K_s:
                    run_shop_screen(ui)


def wait_for_key(ui):
    waiting = True
    while waiting:
        ui.game.clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
                ui.game.running = False
            if event.type == pygame.KEYUP:
                waiting = False
