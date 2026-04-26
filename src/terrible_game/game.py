import pygame
import json
import os
import math
import random
from .settings import *
from .player import Player
from .sprites import Projectile, TeleportPad
from .level import SpawnManager
from .ui import UI

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
        self.coop = False
        self.player2 = None
        self.level_up_player = None
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

        self._place_teleport_pairs()
        self.player2 = None
        self.player = Player(self, seat=0)
        self.all_sprites.add(self.player)
        if self.coop:
            self.player2 = Player(self, seat=1)
            self.player2.pos = vec(self.player.pos.x + 70, self.player.pos.y)
            self.player2.rect.center = (int(self.player2.pos.x), int(self.player2.pos.y))
            self.all_sprites.add(self.player2)

        self.spawn_manager = SpawnManager(self)

        self.is_leveling_up = False
        self.upgrade_options = []
        self.level_up_player = None

        self.run()

    def get_players(self):
        if getattr(self, "player2", None):
            return [self.player, self.player2]
        return [self.player]

    def camera_center(self):
        players = self.get_players()
        s = vec(0, 0)
        for p in players:
            s += p.pos
        return s / len(players)

    def spawn_anchor(self):
        c = self.camera_center()
        return c.x, c.y

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

    def trigger_level_up(self, subject):
        self.is_leveling_up = True
        self.level_up_player = subject

        from .weapons import (
            CalculatorLaser,
            CoffeeBomb,
            MarkerSpray,
            NotebookMissiles,
            PencilWand,
            RulerWave,
            StaplerBurst,
            StickyNotes,
            TextbookOrbit,
            USBBoomerang,
        )
        all_weapons = [
            PencilWand,
            CoffeeBomb,
            TextbookOrbit,
            MarkerSpray,
            StaplerBurst,
            CalculatorLaser,
            USBBoomerang,
            StickyNotes,
            NotebookMissiles,
            RulerWave,
        ]
        owned_weapons = {type(w): w for w in subject.weapons}

        possible_upgrades = []

        for w_class in all_weapons:
            if w_class not in owned_weapons and len(subject.weapons) < MAX_WEAPON_SLOTS:
                possible_upgrades.append(
                    {
                        "title": f"New: {w_class.name}",
                        "desc": w_class.description,
                        "action": lambda wc=w_class, s=subject: s.weapons.append(
                            wc(self, s)
                        ),
                    }
                )

        for w in subject.weapons:
            if w.level < w.max_level:
                possible_upgrades.append(
                    {
                        "title": f"Upgrade: {w.name}",
                        "desc": f"Increase {w.name} to Level {w.level + 1}",
                        "action": lambda w=w: setattr(w, "level", w.level + 1),
                    }
                )

        possible_upgrades.extend(
            [
                {
                    "title": "Caffeine Rush",
                    "desc": "+20% Fire Rate",
                    "action": lambda s=subject: s.passive_stats.update(
                        {
                            "firerate_mult": s.passive_stats["firerate_mult"]
                            * 0.8
                        }
                    ),
                },
                {
                    "title": "All-Nighter",
                    "desc": "+20% Move Speed",
                    "action": lambda s=subject: s.passive_stats.update(
                        {
                            "speed_mult": s.passive_stats["speed_mult"]
                            * 1.2
                        }
                    ),
                },
            ]
        )
        
        if len(possible_upgrades) > 3:
            chosen = random.sample(possible_upgrades, 3)
        else:
            chosen = possible_upgrades
            
        self.upgrade_options = [(opt["title"], opt["desc"], opt["action"]) for opt in chosen]

    def select_upgrade(self, index):
        if 0 <= index < len(self.upgrade_options):
            self.upgrade_options[index][2]()
            self.is_leveling_up = False
            self.level_up_player = None

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            if not self.is_leveling_up:
                self.update()
            self.draw()

        time_survived = (pygame.time.get_ticks() - self.start_time) // 1000
        combined = self.player.score + (
            self.player2.score if getattr(self, "player2", None) else 0
        )
        if combined > self.highscore:
            self.highscore = combined
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
                subj = getattr(self, "level_up_player", self.player)
                idx = None
                if subj is self.player:
                    if event.key == pygame.K_1:
                        idx = 0
                    elif event.key == pygame.K_2:
                        idx = 1
                    elif event.key == pygame.K_3:
                        idx = 2
                elif getattr(self, "player2", None) and subj is self.player2:
                    if event.key in (pygame.K_i, pygame.K_KP1):
                        idx = 0
                    elif event.key in (pygame.K_o, pygame.K_KP2):
                        idx = 1
                    elif event.key in (pygame.K_p, pygame.K_KP3):
                        idx = 2
                if idx is not None:
                    self.select_upgrade(idx)

    def update(self):
        self.spawn_manager.update()

        for pl in self.get_players():
            for weapon in pl.weapons:
                weapon.update()

        self.all_sprites.update()

        self.cleanup_sprites()
        self.handle_collisions()

        for pl in self.get_players():
            pl.energy -= ENERGY_DRAIN_PER_FRAME
        if all(pl.energy <= 0 for pl in self.get_players()):
            self.playing = False

    def cleanup_sprites(self):
        mid = self.camera_center()
        for sprite in self.all_sprites:
            if hasattr(sprite, 'pos') and not getattr(
                sprite, "world_static", False
            ):
                if mid.distance_to(sprite.pos) > 2500:
                    sprite.kill()

    def handle_collisions(self):
        for proj in self.projectiles:
            hits = pygame.sprite.spritecollide(proj, self.enemies, False)
            for enemy in hits:
                if enemy not in proj.hit_enemies:
                    proj.hit_enemies.add(enemy)
                    if (
                        hasattr(enemy, "apply_knockback")
                        and proj.vel.length() > 0.25
                    ):
                        enemy.apply_knockback(proj.vel, magnitude=KNOCKBACK_BASE * 0.9)
                    killed = enemy.take_damage(proj.damage)
                    if killed:
                        cred = getattr(proj, "owner", None) or self.player
                        cred.score += 50
                    proj.pierce_count -= 1
                    if proj.pierce_count <= 0:
                        proj.kill()
                        break

        for pl in self.get_players():
            gem_hits = pygame.sprite.spritecollide(pl, self.gems, True)
            for gem in gem_hits:
                pl.gain_xp(gem.value)

        for pl in self.get_players():
            coin_hits = pygame.sprite.spritecollide(pl, self.coins, True)
            for _ in coin_hits:
                self.session_coins += 1

        for pl in self.get_players():
            item_hits = pygame.sprite.spritecollide(pl, self.items, True)
            for item in item_hits:
                if hasattr(item, 'type'):
                    if item.type == 'chest':
                        pl.score += 200
                        upgradable_weapons = [w for w in pl.weapons if w.level < w.max_level]
                        if upgradable_weapons:
                            w = random.choice(upgradable_weapons)
                            w.level += 1
                            print(f"Chest upgraded {w.name} to level {w.level}!")
                    else:
                        pl.score += 50
                        pl.powerup = item.type
                        pl.powerup_time = pygame.time.get_ticks() + 10000
                else:
                    pl.score += 10
                    pl.energy = min(
                        pl.max_energy, pl.energy + 20
                    )

        for pl in self.get_players():
            enemy_hits = pygame.sprite.spritecollide(pl, self.enemies, False)
            if enemy_hits:
                for enemy in enemy_hits:
                    if pl.powerup == 'shield':
                        enemy.take_damage(999)
                        pl.score += 50
                    else:
                        pl.energy -= PLAYER_ENEMY_TOUCH_DAMAGE
                        enemy.kill()

        for pl in self.get_players():
            enemy_proj_hits = pygame.sprite.spritecollide(pl, self.enemy_projectiles, True)
            if enemy_proj_hits:
                for proj in enemy_proj_hits:
                    if pl.powerup != 'shield':
                        pl.energy -= ENEMY_BULLET_DAMAGE

        self._handle_teleports()

    def _handle_teleports(self):
        now = pygame.time.get_ticks()
        for pl in self.get_players():
            if now < pl.teleport_lock_until:
                continue
            hits = pygame.sprite.spritecollide(pl, self.teleporters, False)
            if not hits:
                continue
            pad = hits[0]
            to = pad.dest
            nudge = to - pad.pos
            if nudge.length() < 0.01:
                nudge = vec(1.0, 0.0)
            else:
                nudge = nudge.normalize() * TELEPORT_NUDGE
            pl.pos = to + nudge
            pl.rect.center = (int(pl.pos.x), int(pl.pos.y))
            pl.teleport_lock_until = now + TELEPORT_COOLDOWN_MS

    def draw(self):
        current_zone = self.spawn_manager.get_current_zone()
        self.screen.fill(current_zone["bg_color"])

        cam = self.camera_center()
        camera_offset_x = cam.x - WIDTH / 2
        camera_offset_y = cam.y - HEIGHT / 2

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
