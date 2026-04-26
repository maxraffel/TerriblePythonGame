import pygame
from .settings import *
import os

vec = pygame.math.Vector2

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        try:
            self.image = pygame.image.load(os.path.join("assets", "player.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (40, 60))
        except Exception:
            self.image = pygame.Surface((40, 60))
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        
        self.pos = vec(WIDTH / 2, HEIGHT / 2)
        self.vel = vec(0, 0)
        
        self.score = 0
        self.energy = 100
        
        self.powerup = None
        self.powerup_time = 0

        # XP and Upgrades
        self.level = 1
        self.xp = 0
        self.next_level_xp = 10
        self.upgrade_projectiles = 1
        self.upgrade_pierce = 1
        self.upgrade_firerate = 1.0
        self.upgrade_speed = 1.0
        self.upgrade_damage = 1

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = int(self.next_level_xp * 1.5)
            self.game.trigger_level_up()

    def update(self):
        if self.powerup and pygame.time.get_ticks() > self.powerup_time:
            self.powerup = None

        self.vel = vec(0, 0)
        keys = pygame.key.get_pressed()
        
        speed = PLAYER_SPEED * self.upgrade_speed
        if self.powerup == 'speed':
            speed *= 2

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel.x = -speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel.x = speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.vel.y = -speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.vel.y = speed

        if self.vel.length() > 0:
            self.vel = self.vel.normalize() * speed

        self.pos += self.vel
        self.rect.center = self.pos
