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

        self.dash_frames_left = 0
        self.dash_vel = vec(0, 0)
        self.dash_cooldown_until = 0
        self.invulnerable_until = 0
        self._prev_lshift = False
        self._last_move_dir = vec(1.0, 0.0)

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

    def _attempt_dash(self, now, raw_move: vec):
        if self.dash_frames_left > 0:
            return
        if now < self.dash_cooldown_until:
            return
        d = vec(raw_move.x, raw_move.y)
        if d.length() < 0.01:
            d = self._last_move_dir
        if d.length() < 0.01:
            return
        d = d.normalize()
        speed = PLAYER_SPEED * self.passive_stats.get('speed_mult', 1.0)
        if self.powerup == 'speed':
            speed *= 2
        self.dash_vel = d * (speed * DASH_SPEED_MULT)
        self.dash_frames_left = DASH_DURATION_FRAMES
        self.dash_cooldown_until = now + DASH_COOLDOWN_MS
        self.invulnerable_until = now + DASH_IFRAMES_MS

    def update(self):
        now = pygame.time.get_ticks()
        if self.powerup and now > self.powerup_time:
            self.powerup = None

        keys = pygame.key.get_pressed()
        raw_move = vec(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            raw_move.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            raw_move.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            raw_move.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            raw_move.y += 1
        if raw_move.length() > 0.01:
            self._last_move_dir = raw_move.normalize()

        lshift = keys[pygame.K_LSHIFT]
        if lshift and not self._prev_lshift:
            self._attempt_dash(now, raw_move)
        self._prev_lshift = bool(lshift)

        if self.dash_frames_left > 0:
            self.pos += self.dash_vel
            self.dash_frames_left -= 1
            self.rect.center = self.pos
            return

        self.vel = vec(0, 0)
        speed = PLAYER_SPEED * self.passive_stats.get('speed_mult', 1.0)
        if self.powerup == 'speed':
            speed *= 2

        if raw_move.x:
            self.vel.x = raw_move.x * speed
        if raw_move.y:
            self.vel.y = raw_move.y * speed

        if self.vel.length() > 0:
            self.vel = self.vel.normalize() * speed

        self.pos += self.vel
        self.rect.center = self.pos
