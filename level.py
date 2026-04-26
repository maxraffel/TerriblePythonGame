import pygame
import random
import math
from sprites import EnergyDrink, SleepMonster, FastMonster, FlyingMonster, TankMonster, SwarmMonster, Powerup
from settings import *

class SpawnManager:
    def __init__(self, game):
        self.game = game
        self.last_spawn_time = pygame.time.get_ticks()
        
    def get_current_zone(self):
        current_time = pygame.time.get_ticks() - self.game.start_time
        current_zone = ZONES[0]
        for zone in ZONES:
            if current_time >= zone["time_thresh"]:
                current_zone = zone
        return current_zone

    def update(self):
        now = pygame.time.get_ticks()
        zone = self.get_current_zone()
        
        if now - self.last_spawn_time > zone["enemy_spawn_rate"]:
            self.last_spawn_time = now
            self.spawn_batch(zone)
            
    def spawn_batch(self, zone):
        if zone["name"] == "Evening":
            batch_size = random.randint(1, 3)
        elif zone["name"] == "Midnight":
            batch_size = random.randint(3, 8)
        elif zone["name"] == "3 AM":
            batch_size = random.randint(5, 15)
        else:
            batch_size = random.randint(10, 25)

        for _ in range(batch_size):
            self.spawn_entity(zone)
            
        if random.random() < 0.05 and zone["name"] != "Evening":
            self.spawn_swarm_ring()

    def spawn_entity(self, zone):
        angle = random.uniform(0, math.pi * 2)
        radius = random.uniform(900, 1100)
        spawn_x = self.game.player.pos.x + math.cos(angle) * radius
        spawn_y = self.game.player.pos.y + math.sin(angle) * radius
        
        if random.random() < zone["drink_chance"]:
            if random.random() < 0.1:
                ptype = random.choice(['speed', 'shield'])
                p = Powerup(spawn_x, spawn_y, ptype)
                self.game.items.add(p)
                self.game.all_sprites.add(p)
            else:
                e = EnergyDrink(spawn_x, spawn_y)
                self.game.items.add(e)
                self.game.all_sprites.add(e)
        else:
            weights = [0.6, 0.2, 0.1, 0.05, 0.05]
            if zone["name"] == "Evening":
                weights = [0.8, 0.2, 0.0, 0.0, 0.0]
            elif zone["name"] == "Midnight":
                weights = [0.6, 0.2, 0.1, 0.1, 0.0]
                
            enemy_type = random.choices([SleepMonster, FastMonster, FlyingMonster, TankMonster, SwarmMonster], weights=weights, k=1)[0]
            m = enemy_type(self.game, spawn_x, spawn_y)
            self.game.enemies.add(m)
            self.game.all_sprites.add(m)

    def spawn_swarm_ring(self):
        num_enemies = 30
        radius = 1200
        for i in range(num_enemies):
            angle = (math.pi * 2 / num_enemies) * i
            spawn_x = self.game.player.pos.x + math.cos(angle) * radius
            spawn_y = self.game.player.pos.y + math.sin(angle) * radius
            m = SwarmMonster(self.game, spawn_x, spawn_y)
            self.game.enemies.add(m)
            self.game.all_sprites.add(m)
