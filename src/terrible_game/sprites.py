import pygame
from .settings import *
import os
import random
import math

vec = pygame.math.Vector2

class Gem(pygame.sprite.Sprite):
    def __init__(self, x, y, value=1):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((0, 100, 255))
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos
        self.value = value

    def update(self):
        pass

class EnergyDrink(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.image = pygame.image.load(os.path.join("assets", "energy_drink.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (40, 40))
        except Exception:
            self.image = pygame.Surface((30, 30))
            self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Powerup(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.type = type
        self.image = pygame.Surface((30, 30))
        if self.type == 'speed':
            self.image.fill(YELLOW)
        else:
            self.image.fill(CYAN)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class SleepMonster(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.setup_image()
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos
        self.speed = random.uniform(1.5, 2.5)
        self.health = 2

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
            gem = Gem(self.pos.x, self.pos.y, 1)
            self.game.gems.add(gem)
            self.game.all_sprites.add(gem)
            self.kill()
            return True
        return False

    def update(self):
        dir = self.game.player.pos - self.pos
        if dir.length() > 0:
            dir = dir.normalize()
        self.pos += dir * self.speed
        self.rect.center = self.pos

class FastMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.speed = random.uniform(3.5, 4.5)
        self.health = 1
        
    def setup_image(self):
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 128, 0))

class TankMonster(SleepMonster):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
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
        
    def setup_image(self):
        self.image = pygame.Surface((20, 20))
        self.image.fill((200, 0, 200))

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
        base_dir = self.game.player.pos - self.pos
        if base_dir.length() > 0:
            base_dir = base_dir.normalize()
        ortho = vec(-base_dir.y, base_dir.x)
        self.time += 0.1
        wave = ortho * math.sin(self.time) * 2
        self.pos += (base_dir * self.speed) + wave
        self.rect.center = self.pos

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_dir, pierce_count, damage):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos
        self.vel = target_dir * PROJECTILE_SPEED
        self.pierce_count = pierce_count
        self.damage = damage
        self.hit_enemies = set()

    def update(self):
        self.pos += self.vel
        self.rect.center = self.pos
