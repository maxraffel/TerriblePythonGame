import pygame
from .settings import *
from .characters import starting_weapon_class
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
        gup = self.game.global_upgrades
        spd_lv = gup.get('speed', 0)
        dmg_lv = gup.get('damage', 0)
        en_lv = gup.get('energy', 0)
        self.max_energy = 100 + 20 * en_lv
        self.energy = self.max_energy
        
        self.powerup = None
        self.powerup_time = 0
        self.teleport_lock_until = 0

        # XP and Upgrades
        self.level = 1
        self.xp = 0
        self.next_level_xp = 10
        
        self.passive_stats = {
            'speed_mult': 1.0 + 0.1 * spd_lv,
            'firerate_mult': 1.0,
            'damage_bonus': dmg_lv
        }
        # So starting weapons (e.g. TextbookOrbit) can use game.player in __init__ / get_stats
        self.game.player = self
        w_cls = starting_weapon_class(
            getattr(self.game, "selected_character_index", 0)
        )
        self.weapons = [w_cls(self.game)]

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = int(self.next_level_xp * 1.5)
            self.game.trigger_level_up()

    def _current_move_speed(self):
        speed = PLAYER_SPEED * self.passive_stats.get("speed_mult", 1.0)
        if self.powerup == "speed":
            speed *= 2
        return speed

    @staticmethod
    def _axis_from_keys(keys, neg_keys, pos_keys):
        for k in neg_keys:
            if keys[k]:
                return -1
        for k in pos_keys:
            if keys[k]:
                return 1
        return 0

    def _velocity_from_input(self, speed):
        keys = pygame.key.get_pressed()
        self.vel = vec(
            speed * self._axis_from_keys(keys, (pygame.K_LEFT, pygame.K_a), (pygame.K_RIGHT, pygame.K_d)),
            speed * self._axis_from_keys(keys, (pygame.K_UP, pygame.K_w), (pygame.K_DOWN, pygame.K_s)),
        )
        if self.vel.length() > 0:
            self.vel = self.vel.normalize() * speed

    def update(self):
        if self.powerup and pygame.time.get_ticks() > self.powerup_time:
            self.powerup = None

        self._velocity_from_input(self._current_move_speed())
        self.pos += self.vel
        self.rect.center = self.pos
