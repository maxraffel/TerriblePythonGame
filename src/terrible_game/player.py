import pygame
from .settings import *
from .characters import starting_weapon_class
import os

vec = pygame.math.Vector2

class Player(pygame.sprite.Sprite):
    def __init__(self, game, player_id=0, pos_offset=None):
        super().__init__()
        self.game = game
        self.player_id = player_id
        try:
            self.image = pygame.image.load(os.path.join("assets", "player.png")).convert_alpha()
            self.image = pygame.transform.scale(self.image, (40, 60))
        except Exception:
            self.image = pygame.Surface((40, 60))
            self.image.fill(YELLOW)
        if player_id == 1:
            tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            tint.fill((0, 200, 255, 90))
            self.image.blit(tint, (0, 0))
        self.rect = self.image.get_rect()
        base = vec(WIDTH / 2, HEIGHT / 2)
        if pos_offset is not None:
            base += pos_offset
        self.pos = base
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
        if self.player_id == 0:
            self.game.player = self
        w_cls = starting_weapon_class(
            getattr(self.game, "selected_character_index", 0)
        )
        self.weapons = [w_cls(self.game, owner=self)]

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = int(self.next_level_xp * 1.5)
            self.game.leveling_player = self
            self.game.trigger_level_up()

    def update(self):
        if self.powerup and pygame.time.get_ticks() > self.powerup_time:
            self.powerup = None

        self.vel = vec(0, 0)
        keys = pygame.key.get_pressed()
        coop = getattr(self.game, "coop_mode", False) and len(
            getattr(self.game, "all_players", [self])
        ) > 1

        speed = PLAYER_SPEED * self.passive_stats.get('speed_mult', 1.0)
        if self.powerup == 'speed':
            speed *= 2

        if self.player_id == 0:
            left = keys[pygame.K_a] or (not coop and keys[pygame.K_LEFT])
            right = keys[pygame.K_d] or (not coop and keys[pygame.K_RIGHT])
            up = keys[pygame.K_w] or (not coop and keys[pygame.K_UP])
            down = keys[pygame.K_s] or (not coop and keys[pygame.K_DOWN])
        else:
            left = keys[pygame.K_LEFT]
            right = keys[pygame.K_RIGHT]
            up = keys[pygame.K_UP]
            down = keys[pygame.K_DOWN]

        if left:
            self.vel.x = -speed
        if right:
            self.vel.x = speed
        if up:
            self.vel.y = -speed
        if down:
            self.vel.y = speed

        if self.vel.length() > 0:
            self.vel = self.vel.normalize() * speed

        self.pos += self.vel
        self.rect.center = self.pos
