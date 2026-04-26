import pygame
import json
import os
import math
import random
from settings import *
from player import Player
from sprites import Projectile
from level import SpawnManager
from ui import UI

vec = pygame.math.Vector2

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.load_data()
        self.ui = UI(self)

    def load_data(self):
        self.dir = os.path.dirname(__file__)
        try:
            with open(os.path.join(self.dir, 'highscore.json'), 'r') as f:
                data = json.load(f)
                self.highscore = data.get('score', 0)
                self.hightime = data.get('time', 0)
        except Exception:
            self.highscore = 0
            self.hightime = 0

    def save_data(self):
        with open(os.path.join(self.dir, 'highscore.json'), 'w') as f:
            json.dump({'score': self.highscore, 'time': self.hightime}, f)

    def new(self):
        self.all_sprites = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.gems = pygame.sprite.Group()

        self.start_time = pygame.time.get_ticks()
        self.last_shot = self.start_time

        self.spawn_manager = SpawnManager(self)
        self.player = Player(self)
        self.all_sprites.add(self.player)

        self.is_leveling_up = False
        self.upgrade_options = []

        self.run()

    def trigger_level_up(self):
        self.is_leveling_up = True
        options = [
            ("Extra Shot", "+1 Projectile", lambda: setattr(self.player, 'upgrade_projectiles', self.player.upgrade_projectiles + 1)),
            ("Caffeine Rush", "+20% Fire Rate", lambda: setattr(self.player, 'upgrade_firerate', self.player.upgrade_firerate * 0.8)),
            ("All-Nighter", "+20% Move Speed", lambda: setattr(self.player, 'upgrade_speed', self.player.upgrade_speed * 1.2)),
            ("Piercing", "Projectiles pierce +1 enemy", lambda: setattr(self.player, 'upgrade_pierce', self.player.upgrade_pierce + 1)),
            ("Heavy Textbooks", "+1 Damage", lambda: setattr(self.player, 'upgrade_damage', self.player.upgrade_damage + 1))
        ]
        self.upgrade_options = random.sample(options, 3)

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

    def auto_shoot(self):
        now = pygame.time.get_ticks()
        current_fire_rate = FIRE_RATE * self.player.upgrade_firerate
        if now - self.last_shot > current_fire_rate:
            if not self.enemies:
                return
            
            nearest_enemy = None
            min_dist = float('inf')
            for enemy in self.enemies:
                dist = self.player.pos.distance_to(enemy.pos)
                if dist < min_dist:
                    min_dist = dist
                    nearest_enemy = enemy
                    
            if nearest_enemy:
                self.last_shot = now
                base_dir = (nearest_enemy.pos - self.player.pos)
                if base_dir.length() > 0:
                    base_dir = base_dir.normalize()
                else:
                    base_dir = vec(1, 0)
                
                count = self.player.upgrade_projectiles
                spread_angle = 15
                
                for i in range(count):
                    angle_offset = (i - (count - 1) / 2) * spread_angle
                    dir = base_dir.rotate(angle_offset)
                    p = Projectile(self.player.rect.centerx, self.player.rect.centery, dir, self.player.upgrade_pierce, self.player.upgrade_damage)
                    self.projectiles.add(p)
                    self.all_sprites.add(p)

    def update(self):
        self.spawn_manager.update()
        self.auto_shoot()
        self.all_sprites.update()
        
        self.cleanup_sprites()
        self.handle_collisions()

        self.player.energy -= 0.05
        if self.player.energy <= 0:
            self.playing = False

    def cleanup_sprites(self):
        for sprite in self.all_sprites:
            if hasattr(sprite, 'pos'):
                if self.player.pos.distance_to(sprite.pos) > 2500:
                    sprite.kill()

    def handle_collisions(self):
        for proj in self.projectiles:
            hits = pygame.sprite.spritecollide(proj, self.enemies, False)
            for enemy in hits:
                if enemy not in proj.hit_enemies:
                    proj.hit_enemies.add(enemy)
                    killed = enemy.take_damage(proj.damage)
                    if killed:
                        self.player.score += 50
                    proj.pierce_count -= 1
                    if proj.pierce_count <= 0:
                        proj.kill()
                        break

        gem_hits = pygame.sprite.spritecollide(self.player, self.gems, True)
        for gem in gem_hits:
            self.player.gain_xp(gem.value)

        item_hits = pygame.sprite.spritecollide(self.player, self.items, True)
        for item in item_hits:
            if hasattr(item, 'type'):
                self.player.score += 50
                self.player.powerup = item.type
                self.player.powerup_time = pygame.time.get_ticks() + 10000
            else:
                self.player.score += 10
                self.player.energy = min(100, self.player.energy + 20)

        enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if enemy_hits:
            for enemy in enemy_hits:
                if self.player.powerup == 'shield':
                    enemy.take_damage(999)
                    self.player.score += 50
                else:
                    self.player.energy -= 30
                    enemy.kill()

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
