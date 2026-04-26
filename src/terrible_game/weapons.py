import pygame
import math
import random
from .settings import *
from .sprites import Projectile

vec = pygame.math.Vector2

class Weapon:
    ui_color = (140, 140, 150)

    def __init__(self, game, owner=None):
        self.game = game
        self.owner = owner if owner is not None else getattr(game, "player", None)
        self.level = 1
        self.max_level = 5

    def update(self):
        pass

class PencilWand(Weapon):
    name = "Pencil Wand"
    description = "Fires pencils at the nearest enemy."

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last_shot = pygame.time.get_ticks()
        
    def get_stats(self):
        # Stats scale with weapon level and global passive stats
        count = 1 + (self.level // 2)
        pierce = 1 + (self.level // 3)
        bonus = int(self.owner.passive_stats.get('damage_bonus', 0))
        damage = 1 + (self.level - 1) + bonus
        fire_rate = FIRE_RATE * max(0.2, (1.0 - (self.level * 0.05))) * self.owner.passive_stats.get('firerate_mult', 1.0)
        return count, pierce, damage, fire_rate

    def update(self):
        now = pygame.time.get_ticks()
        count, pierce, damage, fire_rate = self.get_stats()
        
        if now - self.last_shot > fire_rate:
            if not self.game.enemies:
                return
            
            nearest_enemy = None
            min_dist = float('inf')
            for enemy in self.game.enemies:
                dist = self.owner.pos.distance_to(enemy.pos)
                if dist < min_dist:
                    min_dist = dist
                    nearest_enemy = enemy
                    
            if nearest_enemy:
                self.last_shot = now
                base_dir = (nearest_enemy.pos - self.owner.pos)
                if base_dir.length() > 0:
                    base_dir = base_dir.normalize()
                else:
                    base_dir = vec(1, 0)
                
                spread_angle = 15
                
                for i in range(count):
                    angle_offset = (i - (count - 1) / 2) * spread_angle
                    dir = base_dir.rotate(angle_offset)
                    grav = vec(0, PENCIL_GRAVITY)
                    p = Projectile(
                        self.owner.rect.centerx,
                        self.owner.rect.centery,
                        dir,
                        pierce,
                        damage,
                        gravity=grav,
                        score_owner=self.owner,
                    )
                    self.game.projectiles.add(p)
                    self.game.all_sprites.add(p)

class BombExplosion(pygame.sprite.Sprite):
    def __init__(self, game, x, y, radius, damage, score_owner=None):
        super().__init__()
        self.game = game
        self._score_player = score_owner or getattr(game, "player", None)
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 100, 0, 150), (radius, radius), radius)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = vec(x, y)
        self.radius = radius
        self.damage = damage
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 200 # explosion lingers for 200ms
        
        # Deal damage immediately upon spawn
        self.deal_damage()

    def deal_damage(self):
        for enemy in self.game.enemies:
            dist = enemy.pos.distance_to(self.pos)
            if dist <= self.radius:
                d = enemy.pos - self.pos
                if d.length() > 0.01:
                    if hasattr(enemy, "apply_knockback"):
                        falloff = 1.0 - (dist / max(1, self.radius))
                        enemy.apply_knockback(d, magnitude=BOMB_KNOCKBACK * (0.4 + 0.6 * falloff))
                killed = enemy.take_damage(self.damage)
                if killed and self._score_player is not None:
                    self._score_player.score += 50

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > self.duration:
            self.kill()

class DroppedBomb(pygame.sprite.Sprite):
    def __init__(self, game, x, y, fuse_time, radius, damage, score_owner=None):
        super().__init__()
        self.game = game
        self.score_owner = score_owner or getattr(game, "player", None)
        self.image = pygame.Surface((20, 20))
        self.image.fill((50, 20, 10))
        pygame.draw.circle(self.image, (255, 50, 0), (10, 10), 6)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = vec(x, y)
        angle = random.uniform(0, math.pi * 2)
        sp = random.uniform(0.4, 1.0) * BOMB_TOSS_MAX_SPEED
        self.vel = vec(math.cos(angle) * sp, math.sin(angle) * sp)
        self.fuse_time = fuse_time
        self.radius = radius
        self.damage = damage
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        self.vel *= BOMB_DRAG
        self.pos += self.vel
        self.rect.center = self.pos
        if pygame.time.get_ticks() - self.spawn_time > self.fuse_time:
            exp = BombExplosion(
                self.game,
                self.pos.x,
                self.pos.y,
                self.radius,
                self.damage,
                score_owner=self.score_owner,
            )
            self.game.all_sprites.add(exp)
            self.kill()

class CoffeeBomb(Weapon):
    name = "Coffee Bomb"
    description = "Tosses tumbling bombs that explode after a short fuse."
    ui_color = (200, 90, 40)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last_drop = pygame.time.get_ticks()

    def get_stats(self):
        cooldown = 3000 * max(0.3, (1.0 - (self.level * 0.1))) * self.owner.passive_stats.get('firerate_mult', 1.0)
        radius = 100 + (self.level * 20)
        bonus = int(self.owner.passive_stats.get('damage_bonus', 0))
        damage = 5 + (self.level * 3) + bonus
        return cooldown, radius, damage

    def update(self):
        now = pygame.time.get_ticks()
        cooldown, radius, damage = self.get_stats()
        
        if now - self.last_drop > cooldown:
            self.last_drop = now
            bomb = DroppedBomb(
                self.game,
                self.owner.pos.x,
                self.owner.pos.y,
                1500,
                radius,
                damage,
                score_owner=self.owner,
            )
            self.game.all_sprites.add(bomb)

class OrbitingBook(pygame.sprite.Sprite):
    def __init__(self, game, angle_offset, radius, speed, damage, owner):
        super().__init__()
        self.game = game
        self.owner = owner
        self.image = pygame.Surface((25, 20))
        self.image.fill((0, 0, 150))
        pygame.draw.rect(self.image, WHITE, (5, 2, 15, 16))
        self.rect = self.image.get_rect()
        self.angle_offset = angle_offset
        self.orbit_radius = radius
        self.orbit_speed = speed
        self.damage = damage
        self.hit_cooldowns = {} # Track when we can hit the same enemy again

    def update(self):
        now = pygame.time.get_ticks()
        # Calculate current angle based on time and offset
        current_angle = self.angle_offset + (now * self.orbit_speed / 1000.0)
        
        # Position relative to player
        target_x = self.owner.pos.x + math.cos(current_angle) * self.orbit_radius
        target_y = self.owner.pos.y + math.sin(current_angle) * self.orbit_radius
        
        self.rect.center = (target_x, target_y)
        
        # Damage collisions
        hits = pygame.sprite.spritecollide(self, self.game.enemies, False)
        for enemy in hits:
            last_hit = self.hit_cooldowns.get(enemy, 0)
            if now - last_hit > 500:  # 0.5s i-frames per enemy per book
                self.hit_cooldowns[enemy] = now
                push = enemy.pos - vec(self.rect.centerx, self.rect.centery)
                if hasattr(enemy, "apply_knockback") and push.length() > 0.01:
                    enemy.apply_knockback(push, magnitude=KNOCKBACK_BASE * 0.6)
                killed = enemy.take_damage(self.damage)
                if killed:
                    self.owner.score += 50
                    
        # Cleanup hit cooldowns for dead enemies
        self.hit_cooldowns = {e: t for e, t in self.hit_cooldowns.items() if e.alive()}

class TextbookOrbit(Weapon):
    name = "Textbook Orbit"
    description = "Books orbit and shove enemies on contact."
    ui_color = (100, 110, 220)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.books = []
        self.update_books()

    def get_stats(self):
        count = 1 + (self.level // 2)
        radius = 80 + (self.level * 10)
        speed = 2.0 + (self.level * 0.5)
        bonus = int(self.owner.passive_stats.get('damage_bonus', 0))
        damage = 1 + (self.level // 2) + bonus
        return count, radius, speed, damage

    def update_books(self):
        # Clear existing books
        for book in self.books:
            book.kill()
        self.books.clear()
        
        count, radius, speed, damage = self.get_stats()
        
        for i in range(count):
            angle_offset = (math.pi * 2 / count) * i
            book = OrbitingBook(self.game, angle_offset, radius, speed, damage, self.owner)
            self.game.all_sprites.add(book)
            self.books.append(book)

    def update(self):
        # The OrbitingBooks handle their own movement and collision in their update()
        # We just need to check if stats changed (e.g. leveled up) which we can handle explicitly 
        # or we can check if book count doesn't match expected.
        count, _, _, _ = self.get_stats()
        if len(self.books) != count:
            self.update_books()


def _nearest_enemy(game, from_pos):
    nearest = None
    min_dist = float("inf")
    for enemy in game.enemies:
        d = from_pos.distance_to(enemy.pos)
        if d < min_dist:
            min_dist = d
            nearest = enemy
    return nearest


class USBBoomerangSprite(pygame.sprite.Sprite):
    def __init__(self, game, direction, damage, owner):
        super().__init__()
        self.game = game
        self.owner = owner
        self.image = pygame.Surface((18, 18))
        self.image.fill((30, 180, 120))
        pygame.draw.rect(self.image, WHITE, (3, 3, 12, 12), 2)
        self.rect = self.image.get_rect(center=owner.rect.center)
        self.pos = vec(self.rect.centerx, self.rect.centery)
        self.vel = direction.normalize() * 8.5 if direction.length() > 0 else vec(1, 0) * 8.5
        self.damage = damage
        self.spawn_time = pygame.time.get_ticks()
        self.life_ms = 1700
        self.turn_back_ms = 600
        self.hit_cd = {}

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.turn_back_ms:
            to_player = self.owner.pos - self.pos
            if to_player.length() > 0.01:
                desired = to_player.normalize() * 9.0
                self.vel = self.vel * 0.86 + desired * 0.14
        self.pos += self.vel
        self.rect.center = self.pos

        hits = pygame.sprite.spritecollide(self, self.game.enemies, False)
        for enemy in hits:
            last = self.hit_cd.get(enemy, 0)
            if now - last < 220:
                continue
            self.hit_cd[enemy] = now
            if hasattr(enemy, "apply_knockback") and self.vel.length() > 0.2:
                enemy.apply_knockback(self.vel, magnitude=KNOCKBACK_BASE * 0.7)
            killed = enemy.take_damage(self.damage)
            if killed:
                self.owner.score += 50
        self.hit_cd = {e: t for e, t in self.hit_cd.items() if e.alive()}

        if now - self.spawn_time > self.life_ms:
            self.kill()


class StickyMine(pygame.sprite.Sprite):
    def __init__(self, game, x, y, arm_ms, radius, damage, score_owner=None):
        super().__init__()
        self.game = game
        self.score_owner = score_owner or getattr(game, "player", None)
        self.image = pygame.Surface((14, 14))
        self.image.fill((180, 180, 60))
        pygame.draw.circle(self.image, (70, 70, 20), (7, 7), 3)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = vec(x, y)
        self.arm_ms = arm_ms
        self.radius = radius
        self.damage = damage
        self.spawn = pygame.time.get_ticks()
        self.armed = False

    def update(self):
        now = pygame.time.get_ticks()
        if not self.armed and now - self.spawn >= self.arm_ms:
            self.armed = True
            self.image.fill((235, 180, 70))
            pygame.draw.circle(self.image, RED, (7, 7), 3)
        if not self.armed:
            return
        for enemy in self.game.enemies:
            if enemy.pos.distance_to(self.pos) <= self.radius:
                exp = BombExplosion(
                    self.game,
                    self.pos.x,
                    self.pos.y,
                    self.radius + 10,
                    self.damage,
                    score_owner=self.score_owner,
                )
                self.game.all_sprites.add(exp)
                self.kill()
                return


class NotebookMissile(pygame.sprite.Sprite):
    def __init__(self, game, direction, damage, owner):
        super().__init__()
        self.game = game
        self.owner = owner
        self.image = pygame.Surface((20, 12))
        self.image.fill((70, 120, 255))
        pygame.draw.rect(self.image, WHITE, (2, 2, 16, 8), 1)
        self.rect = self.image.get_rect(center=owner.rect.center)
        self.pos = vec(self.rect.centerx, self.rect.centery)
        self.vel = direction.normalize() * 6.5 if direction.length() > 0 else vec(1, 0) * 6.5
        self.damage = damage
        self.spawn = pygame.time.get_ticks()
        self.life_ms = 2200

    def update(self):
        target = _nearest_enemy(self.game, self.pos)
        if target:
            to = target.pos - self.pos
            if to.length() > 0.01:
                desired = to.normalize() * self.vel.length()
                self.vel = self.vel * 0.88 + desired * 0.12
        self.pos += self.vel
        self.rect.center = self.pos
        hit = pygame.sprite.spritecollideany(self, self.game.enemies)
        if hit:
            if hasattr(hit, "apply_knockback") and self.vel.length() > 0.2:
                hit.apply_knockback(self.vel, magnitude=KNOCKBACK_BASE * 1.0)
            killed = hit.take_damage(self.damage)
            if killed:
                self.owner.score += 50
            self.kill()
            return
        if pygame.time.get_ticks() - self.spawn > self.life_ms:
            self.kill()


class MarkerSpray(Weapon):
    name = "Marker Spray"
    description = "Rapid cone of low-damage marker shots."
    ui_color = (240, 80, 180)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        rate = 260 * self.owner.passive_stats.get("firerate_mult", 1.0)
        if now - self.last_shot <= rate or not self.game.enemies:
            return
        self.last_shot = now
        target = _nearest_enemy(self.game, self.owner.pos)
        if not target:
            return
        base = target.pos - self.owner.pos
        if base.length() == 0:
            base = vec(1, 0)
        base = base.normalize()
        count = 2 + (self.level // 2)
        spread = 26
        damage = max(1, (self.level // 2) + int(self.owner.passive_stats.get("damage_bonus", 0)))
        for i in range(count):
            a = (i - (count - 1) / 2) * spread
            p = Projectile(
                self.owner.pos.x,
                self.owner.pos.y,
                base.rotate(a),
                1,
                damage,
                score_owner=self.owner,
            )
            self.game.projectiles.add(p)
            self.game.all_sprites.add(p)


class StaplerBurst(Weapon):
    name = "Stapler Burst"
    description = "Fires hard-hitting staple bursts."
    ui_color = (190, 190, 200)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        cooldown = 1300 * self.owner.passive_stats.get("firerate_mult", 1.0)
        if now - self.last <= cooldown:
            return
        self.last = now
        target = _nearest_enemy(self.game, self.owner.pos)
        if not target:
            return
        d = target.pos - self.owner.pos
        if d.length() == 0:
            d = vec(1, 0)
        d = d.normalize()
        damage = 4 + self.level + int(self.owner.passive_stats.get("damage_bonus", 0))
        for angle in (-8, 0, 8):
            p = Projectile(
                self.owner.pos.x,
                self.owner.pos.y,
                d.rotate(angle),
                2,
                damage,
                score_owner=self.owner,
            )
            self.game.projectiles.add(p)
            self.game.all_sprites.add(p)


class CalculatorLaser(Weapon):
    name = "Calculator Laser"
    description = "Precise piercing beams with long range."
    ui_color = (80, 240, 240)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        cooldown = (2000 - self.level * 130) * self.owner.passive_stats.get("firerate_mult", 1.0)
        if now - self.last <= max(700, cooldown):
            return
        self.last = now
        target = _nearest_enemy(self.game, self.owner.pos)
        if not target:
            return
        d = target.pos - self.owner.pos
        if d.length() == 0:
            d = vec(1, 0)
        damage = 3 + (self.level * 2) + int(self.owner.passive_stats.get("damage_bonus", 0))
        p = Projectile(
            self.owner.pos.x,
            self.owner.pos.y,
            d.normalize(),
            99,
            damage,
            score_owner=self.owner,
        )
        p.image = pygame.Surface((18, 6))
        p.image.fill((120, 255, 255))
        self.game.projectiles.add(p)
        self.game.all_sprites.add(p)


class USBBoomerang(Weapon):
    name = "USB Boomerang"
    description = "Thrown drives loop back and hit repeatedly."
    ui_color = (30, 180, 120)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        cooldown = (1700 - self.level * 90) * self.owner.passive_stats.get("firerate_mult", 1.0)
        if now - self.last <= max(600, cooldown):
            return
        self.last = now
        target = _nearest_enemy(self.game, self.owner.pos)
        if target:
            d = target.pos - self.owner.pos
        else:
            d = vec(random.uniform(-1, 1), random.uniform(-1, 1))
        dmg = 2 + self.level + int(self.owner.passive_stats.get("damage_bonus", 0))
        b = USBBoomerangSprite(self.game, d, dmg, self.owner)
        self.game.all_sprites.add(b)


class StickyNotes(Weapon):
    name = "Sticky Notes"
    description = "Drops proximity mines around you."
    ui_color = (245, 210, 80)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        cooldown = (2600 - self.level * 120) * self.owner.passive_stats.get("firerate_mult", 1.0)
        if now - self.last <= max(900, cooldown):
            return
        self.last = now
        count = 1 + (self.level // 2)
        radius = 65 + self.level * 8
        dmg = 4 + self.level + int(self.owner.passive_stats.get("damage_bonus", 0))
        for _ in range(count):
            a = random.uniform(0, math.pi * 2)
            r = random.uniform(20, 80)
            x = self.owner.pos.x + math.cos(a) * r
            y = self.owner.pos.y + math.sin(a) * r
            mine = StickyMine(self.game, x, y, 450, radius, dmg, score_owner=self.owner)
            self.game.all_sprites.add(mine)


class NotebookMissiles(Weapon):
    name = "Notebook Missiles"
    description = "Homing pages curve into enemies."
    ui_color = (70, 120, 255)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        cooldown = (1600 - self.level * 100) * self.owner.passive_stats.get("firerate_mult", 1.0)
        if now - self.last <= max(650, cooldown):
            return
        self.last = now
        count = 1 + (self.level // 3)
        dmg = 2 + self.level + int(self.owner.passive_stats.get("damage_bonus", 0))
        target = _nearest_enemy(self.game, self.owner.pos)
        if target:
            base = (target.pos - self.owner.pos)
        else:
            base = vec(1, 0)
        if base.length() == 0:
            base = vec(1, 0)
        base = base.normalize()
        for i in range(count):
            d = base.rotate((i - (count - 1) / 2) * 10)
            m = NotebookMissile(self.game, d, dmg, self.owner)
            self.game.all_sprites.add(m)


class RulerWave(Weapon):
    name = "Ruler Wave"
    description = "Alternating crossfire from ruler angles."
    ui_color = (160, 110, 255)

    def __init__(self, game, owner=None):
        super().__init__(game, owner)
        self.last = pygame.time.get_ticks()
        self.flip = False

    def update(self):
        now = pygame.time.get_ticks()
        cooldown = (1200 - self.level * 70) * self.owner.passive_stats.get("firerate_mult", 1.0)
        if now - self.last <= max(450, cooldown):
            return
        self.last = now
        target = _nearest_enemy(self.game, self.owner.pos)
        if not target:
            return
        base = target.pos - self.owner.pos
        if base.length() == 0:
            base = vec(1, 0)
        base = base.normalize()
        perp = vec(-base.y, base.x)
        damage = 2 + (self.level // 2) + int(self.owner.passive_stats.get("damage_bonus", 0))
        self.flip = not self.flip
        dirs = [base + perp * 0.35, base - perp * 0.35]
        if self.flip:
            dirs.append(base * 0.9 + perp * 0.05)
        for d in dirs:
            p = Projectile(
                self.owner.pos.x,
                self.owner.pos.y,
                d.normalize(),
                2,
                damage,
                score_owner=self.owner,
            )
            self.game.projectiles.add(p)
            self.game.all_sprites.add(p)
