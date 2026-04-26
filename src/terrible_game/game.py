import os

import pygame

from . import game_facade
from .level import SpawnManager
from .persistence import load_progress, save_progress
from .player import Player
from .settings import *
from .ui import UI


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.load_data()
        self.selected_character_index = 0
        self.ui = UI(self)

    def load_data(self):
        self.dir = os.path.dirname(__file__)
        state = load_progress(self.dir)
        self.highscore = state["highscore"]
        self.hightime = state["hightime"]
        self.global_coins = state["global_coins"]
        self.global_upgrades = dict(state["global_upgrades"])
        self.coins_earned_last_run = 0

    def save_data(self):
        save_progress(
            self.dir,
            highscore=self.highscore,
            hightime=self.hightime,
            global_coins=self.global_coins,
            global_upgrades=self.global_upgrades,
        )

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

        self.spawn_manager = SpawnManager(self)
        game_facade.place_default_teleport_pairs(self)
        self.player = Player(self)
        self.all_sprites.add(self.player)

        self.is_leveling_up = False
        self.upgrade_options = []

        self.run()

    def trigger_level_up(self):
        from .level_up_options import build_upgrade_options

        self.is_leveling_up = True
        self.upgrade_options = build_upgrade_options(self)

    def select_upgrade(self, index):
        if 0 <= index < len(self.upgrade_options):
            self.upgrade_options[index][2]()
            self.is_leveling_up = False

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            if not self.is_leveling_up:
                self.update()
            self.draw()

        game_facade.finalize_run(self)

    def events(self):
        game_facade.pump_quit_and_level_up_keys(self)

    def update(self):
        from .collisions import handle_collisions

        self.spawn_manager.update()

        for weapon in self.player.weapons:
            weapon.update()

        self.all_sprites.update()

        game_facade.cull_distant_sprites(self)
        handle_collisions(self)

        self.player.energy -= ENERGY_DRAIN_PER_FRAME
        if self.player.energy <= 0:
            self.playing = False

    def draw(self):
        game_facade.draw_playfield(self)

        if self.is_leveling_up:
            self.ui.draw_level_up()
        else:
            self.ui.draw_hud()

        pygame.display.flip()
