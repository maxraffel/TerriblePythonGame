import pygame
from .settings import *

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
        self.draw_text(f"Energy: {int(self.game.player.energy)}%", 22, GREEN if self.game.player.energy > 30 else RED, 80, 15)

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

    def show_start_screen(self):
        self.game.screen.fill(BGCOLOR)
        self.draw_text("MARIO'S ALL-NIGHTER: SURVIVORS", 48, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("WASD to move! You will shoot automatically.", 22, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Collect blue gems to level up and gain power!", 22, YELLOW, WIDTH / 2, HEIGHT * 5 / 8)
        self.draw_text("Press a key to play", 18, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        pygame.display.flip()
        self.wait_for_key()

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
        
        self.draw_text("Press a key to play again", 18, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        pygame.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        waiting = True
        while waiting:
            self.game.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.game.running = False
                if event.type == pygame.KEYUP:
                    waiting = False
