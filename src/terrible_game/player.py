import pygame
from .settings import *
from .characters import CHARACTERS, starting_weapon_class
import os

vec = pygame.math.Vector2


class Player(pygame.sprite.Sprite):
    def __init__(self, game, seat=0):
        super().__init__()
        self.game = game
        self.seat = seat
        try:
            self.image = pygame.image.load(os.path.join("assets", "player.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (40, 60))
        except Exception:
            self.image = pygame.Surface((40, 60))
            self.image.fill(YELLOW)
        if seat == 1:
            tint = pygame.Surface(self.image.get_size())
            tint.fill((90, 160, 255))
            tint.set_alpha(110)
            self.image.blit(tint, (0, 0))
        self.rect = self.image.get_rect()

        self.pos = vec(WIDTH / 2, HEIGHT / 2)
        if seat == 1:
            self.pos = vec(WIDTH / 2 + 60, HEIGHT / 2)
        self.vel = vec(0, 0)

        self.score = 0
        gup = self.game.global_upgrades
        spd_lv = gup.get("speed", 0)
        dmg_lv = gup.get("damage", 0)
        en_lv = gup.get("energy", 0)
        self.max_energy = 100 + 20 * en_lv
        self.energy = self.max_energy

        self.powerup = None
        self.powerup_time = 0
        self.teleport_lock_until = 0

        self.level = 1
        self.xp = 0
        self.next_level_xp = 10

        self.passive_stats = {
            "speed_mult": 1.0 + 0.1 * spd_lv,
            "firerate_mult": 1.0,
            "damage_bonus": dmg_lv,
        }
        if seat == 0:
            self.game.player = self
        else:
            self.game.player2 = self

        n = max(1, len(CHARACTERS))
        char_idx = (
            getattr(self.game, "selected_character_index", 0)
            if seat == 0
            else (getattr(self.game, "selected_character_index", 0) + 1) % n
        )
        w_cls = starting_weapon_class(char_idx)
        self.weapons = [w_cls(self.game, self)]

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = int(self.next_level_xp * 1.5)
            self.game.trigger_level_up(self)

    def update(self):
        if self.powerup and pygame.time.get_ticks() > self.powerup_time:
            self.powerup = None

        self.vel = vec(0, 0)
        keys = pygame.key.get_pressed()

        speed = PLAYER_SPEED * self.passive_stats.get("speed_mult", 1.0)
        if self.powerup == "speed":
            speed *= 2

        if self.seat == 0:
            if keys[pygame.K_a]:
                self.vel.x = -speed
            if keys[pygame.K_d]:
                self.vel.x = speed
            if keys[pygame.K_w]:
                self.vel.y = -speed
            if keys[pygame.K_s]:
                self.vel.y = speed
        else:
            if keys[pygame.K_LEFT]:
                self.vel.x = -speed
            if keys[pygame.K_RIGHT]:
                self.vel.x = speed
            if keys[pygame.K_UP]:
                self.vel.y = -speed
            if keys[pygame.K_DOWN]:
                self.vel.y = speed

        if self.vel.length() > 0:
            self.vel = self.vel.normalize() * speed

        self.pos += self.vel
        self.rect.center = self.pos
