import pygame
import json
import os
import math
import random
from .settings import *
from .player import Player
from .sprites import TeleportPad
from .level import SpawnManager
from .ui import UI
from .gameplay_handlers import (
    collect_upgrade_options,
    finalize_upgrade_choices,
    handle_collisions,
)

vec = pygame.math.Vector2

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.load_data()
        self.selected_character_index = 0
        self.ui = UI(self)

    def load_data(self):
        self.dir = os.path.dirname(__file__)
        self.global_coins = 0
        self.coins_earned_last_run = 0
        self.global_upgrades = {'damage': 0, 'speed': 0, 'energy': 0}
        try:
            with open(os.path.join(self.dir, 'highscore.json'), 'r') as f:
                data = json.load(f)
                self.highscore = data.get('score', 0)
                self.hightime = data.get('time', 0)
                self.global_coins = int(data.get('global_coins', 0))
                loaded = data.get('global_upgrades') or {}
                for k in self.global_upgrades:
                    if k in loaded:
                        self.global_upgrades[k] = int(loaded[k])
        except Exception:
            self.highscore = 0
            self.hightime = 0

    def save_data(self):
        with open(os.path.join(self.dir, 'highscore.json'), 'w') as f:
            json.dump({
                'score': self.highscore,
                'time': self.hightime,
                'global_coins': self.global_coins,
                'global_upgrades': self.global_upgrades,
            }, f)

    def new(self):
        self.all_sprites = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.gems = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.teleporters = pygame.sprite.Group()
        self.session_coins = 0

        self.start_time = pygame.time.get_ticks()
        self.last_shot = self.start_time

        self.spawn_manager = SpawnManager(self)
        self._place_teleport_pairs()
        self.player = Player(self)
        self.all_sprites.add(self.player)

        self.is_leveling_up = False
        self.upgrade_options = []

        self.run()

    def _place_teleport_pairs(self):
        """
        Three links placed in different map regions. Within each link, the two pads
        are still exactly TELEPORT_PAIR_SPACING apart (horizontal, vertical, or 45°).
        """
        cx, cy = WIDTH // 2, HEIGHT // 2
        s = float(TELEPORT_PAIR_SPACING)
        o = 1.0 / math.sqrt(2.0)
        diag = vec(-s * o, -s * o)

        # Widespread anchors (far from each other); same per-pair offsets as before: (s,0), (0,s), length-s diagonal.
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
                self.teleporters.add(p)
                self.all_sprites.add(p)

    def trigger_level_up(self):
        self.is_leveling_up = True
        possible = collect_upgrade_options(self)
        self.upgrade_options = finalize_upgrade_choices(possible, random)

    def select_upgrade(self, index):
        if 0 <= index < len(self.upgrade_options):
            self.upgrade_options[index][2]()
            self.is_leveling_up = False

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            if not self.is_leveling_up:
                self.update()
            self.draw()

        time_survived = (pygame.time.get_ticks() - self.start_time) // 1000
        if self.player.score > self.highscore:
            self.highscore = self.player.score
        if time_survived > self.hightime:
            self.hightime = time_survived
        self.coins_earned_last_run = self.session_coins
        self.global_coins += self.session_coins
        self.save_data()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pygame.KEYDOWN and self.is_leveling_up:
                if event.key == pygame.K_1:
                    self.select_upgrade(0)
                elif event.key == pygame.K_2:
                    self.select_upgrade(1)
                elif event.key == pygame.K_3:
                    self.select_upgrade(2)

    def update(self):
        self.spawn_manager.update()
        
        for weapon in self.player.weapons:
            weapon.update()
            
        self.all_sprites.update()
        
        self.cleanup_sprites()
        handle_collisions(self)

        self.player.energy -= ENERGY_DRAIN_PER_FRAME
        if self.player.energy <= 0:
            self.playing = False

    def cleanup_sprites(self):
        for sprite in self.all_sprites:
            if hasattr(sprite, 'pos') and not getattr(
                sprite, "world_static", False
            ):
                if self.player.pos.distance_to(sprite.pos) > 2500:
                    sprite.kill()

    def draw(self):
        current_zone = self.spawn_manager.get_current_zone()
        self.screen.fill(current_zone["bg_color"])
        
        camera_offset_x = self.player.pos.x - WIDTH / 2
        camera_offset_y = self.player.pos.y - HEIGHT / 2

        self.draw_floor_grid(camera_offset_x, camera_offset_y)

        for sprite in self.all_sprites:
            screen_pos = (sprite.rect.x - camera_offset_x, sprite.rect.y - camera_offset_y)
            self.screen.blit(sprite.image, screen_pos)
        
        if self.is_leveling_up:
            self.ui.draw_level_up()
        else:
            self.ui.draw_hud()

        pygame.display.flip()

    def draw_floor_grid(self, cam_x, cam_y):
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
                pygame.draw.rect(self.screen, color, (screen_x, screen_y, tile_size, tile_size))
