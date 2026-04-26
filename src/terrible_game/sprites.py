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

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.set_colorkey((0, 0, 0))
        pygame.draw.circle(self.image, (255, 220, 50), (4, 4), 3)
        pygame.draw.circle(self.image, (200, 160, 20), (4, 4), 3, 1)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos

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

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_dir, pierce_count, damage, gravity=None, owner=None):
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
        self.gravity = vec(gravity) if gravity is not None else None
        self.owner = owner

    def update(self):
        if self.gravity is not None:
            self.vel += self.gravity
        self.pos += self.vel
        self.rect.center = self.pos

class Chest(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.type = 'chest'
        self.image = pygame.Surface((30, 30))
        self.image.fill((150, 75, 0)) # Brown
        pygame.draw.rect(self.image, (255, 215, 0), (0, 10, 30, 10)) # Gold band
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class TeleportPad(pygame.sprite.Sprite):
    """Walk into the pad to warp to `dest` (other pad’s center) in the same pair."""

    def __init__(self, x, y, dest):
        super().__init__()
        size = 44
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.world_static = True
        c = (90, 220, 255)
        c2 = (200, 80, 255)
        mid = size // 2
        pygame.draw.circle(self.image, c, (mid, mid), mid - 1)
        pygame.draw.circle(self.image, c2, (mid, mid), mid - 1, 3)
        pygame.draw.circle(self.image, (255, 255, 255), (mid, mid), 6, 2)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.dest = vec(dest)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def update(self):
        self.rect.center = (int(self.pos.x), int(self.pos.y))
