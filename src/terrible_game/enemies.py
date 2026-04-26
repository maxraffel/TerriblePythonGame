import pygame
import os
import random
import math
from .settings import *
from .sprites import Gem, Coin, EnergyDrink, Chest
from .coop_helpers import nearest_player as _nearest_player

vec = pygame.math.Vector2

class SleepMonster(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.setup_image()
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos
        self.kb = vec(0, 0)
        self.kb_resist = 1.0
        self.speed = random.uniform(1.5, 2.5)
        self.health = 2

    def _apply_kb_movement(self):
        self.kb *= KNOCKBACK_FRICTION
        self.pos += self.kb

    def apply_knockback(self, direction, magnitude=KNOCKBACK_BASE):
        if direction.length() < 0.01:
            return
        self.kb += direction.normalize() * (magnitude * self.kb_resist)

    def setup_image(self):
        try:
            self.image = pygame.image.load(os.path.join("assets", "sleep_monster.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (50, 50))
        except Exception:
            self.image = pygame.Surface((40, 40))
            self.image.fill(RED)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            rand = random.random()
            if rand < 0.02:
                item = Chest(self.pos.x, self.pos.y)
                self.game.items.add(item)
                self.game.all_sprites.add(item)
            elif rand < 0.07:
                item = EnergyDrink(self.pos.x, self.pos.y)
                self.game.items.add(item)
                self.game.all_sprites.add(item)
            else:
                if random.random() < 0.10:
                    coin = Coin(self.pos.x, self.pos.y)
                    self.game.coins.add(coin)
                    self.game.all_sprites.add(coin)
                else:
                    gem = Gem(self.pos.x, self.pos.y, 1)
                    self.game.gems.add(gem)
                    self.game.all_sprites.add(gem)
            self.kill()
            return True
        return False

    def update(self):
        self._apply_kb_movement()
        tgt = _nearest_player(self.game, self.pos)
        dir = tgt.pos - self.pos
        if dir.length() > 0:
            dir = dir.normalize()
        self.pos += dir * self.speed
        self.rect.center = self.pos

class FastMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.kb_resist = 0.8
        self.speed = random.uniform(3.5, 4.5)
        self.health = 1
        
    def setup_image(self):
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 128, 0))

class TankMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.kb_resist = 0.2
        self.speed = random.uniform(0.8, 1.2)
        self.health = 15
        
    def setup_image(self):
        self.image = pygame.Surface((80, 80))
        self.image.fill((100, 0, 0))

class SwarmMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.speed = random.uniform(2.5, 3.5)
        self.health = 1
        self.momentum = vec(0, 0)
        self.steer = 0.2
        
    def setup_image(self):
        self.image = pygame.Surface((20, 20))
        self.image.fill((200, 0, 200))

    def update(self):
        self._apply_kb_movement()
        tgt = _nearest_player(self.game, self.pos)
        to = tgt.pos - self.pos
        if to.length() > 0.01:
            self.momentum += to.normalize() * (self.steer * self.speed)
        self.momentum *= 0.9
        cap = self.speed * 1.15
        if self.momentum.length() > cap:
            self.momentum.scale_to_length(cap)
        self.pos += self.momentum
        self.rect.center = self.pos

class FlyingMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.speed = random.uniform(2.0, 3.0)
        self.time = random.uniform(0, math.pi * 2)
        self.health = 2
        
    def setup_image(self):
        self.image = pygame.Surface((40, 40))
        self.image.fill((255, 0, 255))
        
    def update(self):
        self._apply_kb_movement()
        tgt = _nearest_player(self.game, self.pos)
        base_dir = tgt.pos - self.pos
        if base_dir.length() > 0:
            base_dir = base_dir.normalize()
        ortho = vec(-base_dir.y, base_dir.x)
        self.time += 0.1
        wave = ortho * math.sin(self.time) * 2
        self.pos += (base_dir * self.speed) + wave
        self.rect.center = self.pos

class DasherMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.health = 3
        self.state = 'aiming' # 'aiming' or 'dashing'
        self.state_timer = pygame.time.get_ticks()
        self.aim_duration = 1500
        self.dash_duration = 500
        self.dash_speed = 10.0
        self.dash_dir = vec(0, 0)
        
    def setup_image(self):
        self.image = pygame.Surface((35, 35))
        self.image.fill(WHITE)
        pygame.draw.rect(self.image, RED, self.image.get_rect(), 3)
        
    def update(self):
        self._apply_kb_movement()
        now = pygame.time.get_ticks()
        if self.state == 'aiming':
            if now - self.state_timer > self.aim_duration:
                self.state = 'dashing'
                self.state_timer = now
                tgt = _nearest_player(self.game, self.pos)
                dir = tgt.pos - self.pos
                if dir.length() > 0:
                    self.dash_dir = dir.normalize()
            else:
                tgt = _nearest_player(self.game, self.pos)
                dir = tgt.pos - self.pos
                if dir.length() > 0:
                    dir = dir.normalize()
                self.pos += dir * (self.speed * 0.5)
        elif self.state == 'dashing':
            if now - self.state_timer > self.dash_duration:
                self.state = 'aiming'
                self.state_timer = now
            else:
                self.pos += self.dash_dir * self.dash_speed
                
        self.rect.center = self.pos

class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_dir, game, homing_strength=None):
        super().__init__()
        self.game = game
        self.homing_strength = (
            homing_strength
            if homing_strength is not None
            else ENEMY_BULLET_HOMING
        )
        self.image = pygame.Surface((10, 10))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos
        self.vel = target_dir * (PROJECTILE_SPEED * 0.5)

    def update(self):
        if self.homing_strength > 0 and self.game:
            tgt = _nearest_player(self.game, self.pos)
            to = tgt.pos - self.pos
            if to.length() > 8:
                desired = to.normalize() * self.vel.length()
                h = self.homing_strength
                new_v = self.vel * (1.0 - h) + desired * h
                if new_v.length() > 0.1:
                    self.vel = new_v.normalize() * self.vel.length()
        self.pos += self.vel
        self.rect.center = self.pos

class ShooterMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.health = 2
        self.speed = 1.8
        self.ideal_distance = 300
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = 2000
        
    def setup_image(self):
        self.image = pygame.Surface((40, 40))
        self.image.fill((0, 200, 200))
        pygame.draw.circle(self.image, RED, (20, 20), 10)
        
    def update(self):
        self._apply_kb_movement()
        now = pygame.time.get_ticks()
        tgt = _nearest_player(self.game, self.pos)
        dir = tgt.pos - self.pos
        dist = dir.length()
        
        if dist > 0:
            dir_norm = dir.normalize()
            
            # Move towards or away to maintain ideal distance
            if dist > self.ideal_distance + 20:
                self.pos += dir_norm * self.speed
            elif dist < self.ideal_distance - 20:
                self.pos -= dir_norm * self.speed
                
            # Shoot (slightly curving "heat-seeking" slugs)
            if now - self.last_shot > self.shoot_delay:
                self.last_shot = now
                proj = EnemyProjectile(
                    self.pos.x, self.pos.y, dir_norm, self.game
                )
                self.game.enemy_projectiles.add(proj)
                self.game.all_sprites.add(proj)
                
        self.rect.center = self.pos

class BossMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.kb_resist = 0.12
        self.speed = 0.5
        self.health = 100
        self.last_spawn = pygame.time.get_ticks()
        self.spawn_delay = 3000
        
    def setup_image(self):
        self.image = pygame.Surface((150, 150))
        self.image.fill((150, 0, 50))
        pygame.draw.circle(self.image, BLACK, (75, 75), 30)
        
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            # Drop a lot of gems
            for _ in range(20):
                offset_x = random.uniform(-50, 50)
                offset_y = random.uniform(-50, 50)
                gem = Gem(self.pos.x + offset_x, self.pos.y + offset_y, 5)
                self.game.gems.add(gem)
                self.game.all_sprites.add(gem)

            for _ in range(12):
                offset_x = random.uniform(-45, 45)
                offset_y = random.uniform(-45, 45)
                coin = Coin(self.pos.x + offset_x, self.pos.y + offset_y)
                self.game.coins.add(coin)
                self.game.all_sprites.add(coin)
            
            # Guaranteed chest drop
            chest = Chest(self.pos.x, self.pos.y)
            self.game.items.add(chest)
            self.game.all_sprites.add(chest)
            
            self.kill()
            return True
        return False

    def update(self):
        self._apply_kb_movement()
        tgt = _nearest_player(self.game, self.pos)
        dir = tgt.pos - self.pos
        if dir.length() > 0:
            dir = dir.normalize()
        self.pos += dir * self.speed
        self.rect.center = self.pos

        now = pygame.time.get_ticks()
        if now - self.last_spawn > self.spawn_delay:
            self.last_spawn = now
            for _ in range(3):
                offset_x = random.uniform(-30, 30)
                offset_y = random.uniform(-30, 30)
                m = SwarmMonster(self.game, self.pos.x + offset_x, self.pos.y + offset_y)
                self.game.enemies.add(m)
                self.game.all_sprites.add(m)
