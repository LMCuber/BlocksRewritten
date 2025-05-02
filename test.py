import pygame
import sys
import cProfile
import random
from pathlib import Path
from threading import Thread
from markovjunior.markov import Markov


# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)

# constants
pygame.init()

GRID_SIZE = 128
WIDTH = 2 ** 9
HEIGHT = 2 ** 9
TILE_SIZE = WIDTH / GRID_SIZE
KERNEL_SIZE = 3
pygame.display.set_caption("Markov & WFC Testing Module")
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
DIS = pygame.Surface([GRID_SIZE] * 2)
clock = pygame.time.Clock()
TARG_FPS = 60
font = pygame.font.SysFont("Courier New", 20)


markov = Markov(Path("wfc.xml"), [GRID_SIZE] * 2)

def main():
    start_markov = False
    # mainloop
    running = __name__ == "__main__"
    while running:
        clock.tick(TARG_FPS)
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                elif event.key == pygame.K_SPACE:
                    start_markov = True
    
        # clearing window
        DIS.fill((DARK_GRAY))
        WIN.fill((DARK_GRAY))

        if start_markov:
            markov.update()
            markov.render_to_surf(DIS)
        
        # blit auxilary surface onto main window surface
        WIN.blit(pygame.transform.scale_by(DIS, TILE_SIZE), (0, 0))

        # flip the display
        pygame.display.flip()

    pygame.quit()
    sys.exit()


main()
# cProfile.run("main()", sort="cumtime", filename="cprof.out")
# cProfile.run("main()", sort="cumtime")