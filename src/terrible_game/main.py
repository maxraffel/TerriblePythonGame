import pygame
from .game import Game

if __name__ == '__main__':
    g = Game()
    while g.running:
        g.ui.show_start_screen()
        if not g.running:
            break
        g.new()
        if g.running:
            g.ui.show_go_screen()
    pygame.quit()
