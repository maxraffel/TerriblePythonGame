import pygame
from src.terrible_game.main import Game

if __name__ == '__main__':
    g = Game()
    g.ui.show_start_screen()
    while g.running:
        g.new()
        g.ui.show_go_screen()
    pygame.quit()
