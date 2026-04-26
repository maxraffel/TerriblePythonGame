import pygame
from .settings import (
    BGCOLOR,
    BLUE,
    CYAN,
    GREEN,
    MINIMAP_MARGIN,
    MINIMAP_SIZE,
    MINIMAP_WORLD_RADIUS,
    RED,
    SHOP_BASE_COST,
    SHOP_MAX_LEVEL,
    WHITE,
    WIDTH,
    HEIGHT,
    YELLOW,
    FPS,
)
from pygame.math import Vector2
from . import ui_menus

class UI:
    def __init__(self, game):
        self.game = game
        self.font_name = pygame.font.match_font('arial')

    def draw_text(self, text, size, color, x, y):
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.game.screen.blit(text_surface, text_rect)

    def draw_hud(self):
        current_zone = self.game.spawn_manager.get_current_zone()
        time_survived = (pygame.time.get_ticks() - self.game.start_time) // 1000
        mins = time_survived // 60
        secs = time_survived % 60
        
        self.draw_text(f"Time: {mins:02d}:{secs:02d}", 26, WHITE, WIDTH / 2, 40)
        self.draw_text(f"Zone: {current_zone['name']}", 22, WHITE, WIDTH / 2, 70)
        self.draw_text(f"Score: {self.game.player.score}", 22, WHITE, WIDTH / 2, 15)
        e = self.game.player.energy
        em = self.game.player.max_energy
        self.draw_text(
            f"Energy: {int(e)}/{int(em)}",
            22,
            GREEN if e > 0.3 * em else RED,
            80,
            15,
        )
        self.draw_text(
            f"Run coins: {self.game.session_coins}",
            18,
            (255, 220, 100),
            WIDTH - 100,
            15,
        )

        # XP Bar
        bar_width = WIDTH * 0.8
        bar_height = 10
        x = (WIDTH - bar_width) / 2
        y = 5
        fill = (self.game.player.xp / self.game.player.next_level_xp) * bar_width
        outline_rect = pygame.Rect(x, y, bar_width, bar_height)
        fill_rect = pygame.Rect(x, y, fill, bar_height)
        pygame.draw.rect(self.game.screen, BLUE, fill_rect)
        pygame.draw.rect(self.game.screen, WHITE, outline_rect, 2)
        self.draw_text(f"Lv {self.game.player.level}", 18, WHITE, WIDTH - 50, 2)

        if self.game.player.powerup:
            time_left = max(0, (self.game.player.powerup_time - pygame.time.get_ticks()) // 1000)
            name = "ESPRESSO SPEED" if self.game.player.powerup == 'speed' else "COFFEE SHIELD"
            color = (255, 255, 0) if self.game.player.powerup == 'speed' else (0, 255, 255)
            self.draw_text(f"{name}: {time_left}s", 26, color, WIDTH / 2, 110)

        self._draw_weapon_loadout()
        self._draw_minimap()

    @staticmethod
    def _sprite_world_pos(sprite):
        if hasattr(sprite, "pos"):
            return Vector2(sprite.pos)
        return Vector2(sprite.rect.centerx, sprite.rect.centery)

    def _minimap_plot(self, sc, cx, cy, half, scale, rel, color, radius=3):
        d = Vector2(rel.x, rel.y) * scale
        length = d.length()
        if length > half - radius:
            if length < 0.01:
                return
            d = d * ((half - radius) / length)
        pygame.draw.circle(sc, color, (int(cx + d.x), int(cy + d.y)), radius)

    def _minimap_draw_frame(self, sc, ax, ay, size, cx, cy, half):
        pygame.draw.rect(sc, (18, 18, 28), (ax, ay, size, size), border_radius=4)
        pygame.draw.rect(sc, (70, 75, 95), (ax, ay, size, size), 2, border_radius=4)
        pygame.draw.circle(sc, (40, 44, 58), (cx, cy), half, 1)

    def _minimap_plot_layer(self, g, plot, sprites, color, radius):
        p = g.player.pos
        for s in sprites:
            plot(self._sprite_world_pos(s) - p, color, radius)

    def _minimap_plot_items(self, g, plot):
        p = g.player.pos
        for s in g.items:
            rel = self._sprite_world_pos(s) - p
            chest = getattr(s, "type", None) == "chest"
            plot(rel, (170, 110, 55) if chest else (110, 220, 150), 3 if chest else 2)

    def _minimap_legend(self, sc, ax, ay, size):
        title = pygame.font.Font(self.font_name, 12)
        sc.blit(
            title.render("Minimap (relative to you)", True, (150, 155, 170)),
            (ax + 4, ay + 4),
        )
        key = pygame.font.Font(self.font_name, 9)
        sc.blit(
            key.render(
                "E enemy  G gem  $ coin  T tele  ~ bomb/shot",
                True,
                (110, 115, 128),
            ),
            (ax + 4, ay + size - 15),
        )

    def _draw_minimap(self):
        from .weapons import DroppedBomb

        g = self.game
        sc = g.screen
        p = g.player.pos
        size = MINIMAP_SIZE
        margin = MINIMAP_MARGIN
        half = (size // 2) - 3
        world_r = MINIMAP_WORLD_RADIUS
        scale = half / world_r
        cx = int(WIDTH - margin - size // 2)
        cy = int(HEIGHT - margin - size // 2)
        ax, ay = cx - size // 2, cy - size // 2

        self._minimap_draw_frame(sc, ax, ay, size, cx, cy, half)

        def plot(rel, color, radius=3):
            self._minimap_plot(sc, cx, cy, half, scale, rel, color, radius)

        self._minimap_plot_layer(g, plot, g.teleporters, (90, 210, 255), 2)
        self._minimap_plot_layer(g, plot, g.gems, (50, 110, 255), 2)
        self._minimap_plot_layer(g, plot, g.coins, (255, 210, 70), 2)
        self._minimap_plot_items(g, plot)
        for s in g.all_sprites:
            if isinstance(s, DroppedBomb):
                plot(self._sprite_world_pos(s) - p, (255, 95, 40), 2)
        self._minimap_plot_layer(g, plot, g.enemies, (255, 75, 75), 3)
        self._minimap_plot_layer(g, plot, g.enemy_projectiles, (255, 180, 130), 2)

        pygame.draw.circle(sc, (255, 255, 120), (cx, cy), 4)
        pygame.draw.circle(sc, (40, 40, 50), (cx, cy), 4, 1)
        self._minimap_legend(sc, ax, ay, size)

    def _draw_weapon_loadout(self):
        font = pygame.font.Font(self.font_name, 16)
        wps = self.game.player.weapons
        panel = 8
        block = 24 * max(1, len(wps)) + 28
        y0 = HEIGHT - block
        self.game.screen.blit(font.render("Loadout", True, (220, 220, 200)), (panel, y0))
        for i, w in enumerate(wps):
            y = y0 + 22 + i * 24
            col = getattr(w, "ui_color", (150, 150, 150))
            pygame.draw.rect(self.game.screen, col, (panel, y, 16, 16))
            pygame.draw.rect(self.game.screen, WHITE, (panel, y, 16, 16), 1)
            self.game.screen.blit(
                font.render(f"{w.name}  Lv {w.level}", True, WHITE),
                (panel + 22, y - 1),
            )

    def draw_level_up(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.game.screen.blit(overlay, (0, 0))

        self.draw_text("LEVEL UP!", 64, YELLOW, WIDTH / 2, HEIGHT / 4 - 50)
        self.draw_text("Press 1, 2, or 3 to select an upgrade", 22, WHITE, WIDTH / 2, HEIGHT / 4 + 30)

        for i, option in enumerate(self.game.upgrade_options):
            title, desc, _ = option
            y_offset = HEIGHT / 2 + (i - 1) * 100
            
            card_rect = pygame.Rect(WIDTH / 2 - 200, y_offset - 40, 400, 80)
            pygame.draw.rect(self.game.screen, (50, 50, 70), card_rect)
            pygame.draw.rect(self.game.screen, WHITE, card_rect, 2)
            
            self.draw_text(f"{i + 1}. {title}", 28, YELLOW, WIDTH / 2, y_offset - 30)
            self.draw_text(desc, 18, WHITE, WIDTH / 2, y_offset)

    def show_character_select(self) -> bool:
        """Return True if a character was chosen (1/2/3), False if ESC back to title."""
        return ui_menus.run_character_select(self)

    def _wrap_text(self, text, font, max_px):
        words = text.split()
        if not words:
            return [""]
        lines = []
        line = words[0]
        for w in words[1:]:
            test = f"{line} {w}"
            if font.size(test)[0] <= max_px:
                line = test
            else:
                lines.append(line)
                line = w
        lines.append(line)
        return lines[:2]

    def show_start_screen(self):
        ui_menus.run_start_screen(self)

    def _try_buy_upgrade(self, key):
        if self.game.global_upgrades.get(key, 0) >= SHOP_MAX_LEVEL:
            return
        level = self.game.global_upgrades[key]
        cost = SHOP_BASE_COST * (1 + level)
        if self.game.global_coins < cost:
            return
        self.game.global_coins -= cost
        self.game.global_upgrades[key] = level + 1
        self.game.save_data()

    def show_shop_screen(self):
        ui_menus.run_shop_screen(self)

    def show_go_screen(self):
        if not self.game.running:
            return
        self.game.screen.fill(BGCOLOR)
        self.draw_text("GAME OVER", 48, RED, WIDTH / 2, HEIGHT / 4)
        
        time_survived = (pygame.time.get_ticks() - self.game.start_time) // 1000
        mins = time_survived // 60
        secs = time_survived % 60
        
        high_mins = self.game.hightime // 60
        high_secs = self.game.hightime % 60
        
        self.draw_text(f"Score: {self.game.player.score}   |   Time: {mins:02d}:{secs:02d}", 26, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text(f"Level Reached: {self.game.player.level}", 22, YELLOW, WIDTH / 2, HEIGHT / 2 + 30)
        self.draw_text(f"High Score: {self.game.highscore}   |   Max Time: {high_mins:02d}:{high_secs:02d}", 22, GREEN, WIDTH / 2, HEIGHT / 2 + 70)
        earned = getattr(self.game, "coins_earned_last_run", 0)
        self.draw_text(
            f"Coins this run: +{earned}  |  Bank: {self.game.global_coins}",
            20,
            (255, 220, 100),
            WIDTH / 2,
            HEIGHT / 2 + 100,
        )
        
        self.draw_text("Press a key to play again", 18, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        pygame.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        ui_menus.wait_for_key(self)
