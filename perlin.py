import pygame
import sys
import cProfile
import opensimplex as osim


def octave_noise(x, y, freq, amp=1, octaves=1, lac=2, pers=0.5):
    height = 0
    max_value = 0
    for i in range(octaves):
        nx = x * freq
        ny = y * freq
        height += amp * osim.noise2(x=nx, y=ny)

        max_value += amp
        freq *= lac
        amp *= pers

    height = (height + max_value) / (max_value * 2)
    return height


# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)

# constants
pygame.init()
WIDTH = 500
HEIGHT = 500
pygame.display.set_caption("Perlin Test")
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
TARG_FPS = 60


surf = pygame.Surface((500, 500))
for y in range(surf.height):
    for x in range(surf.width):
        height = octave_noise(x, y, 0.01, octaves=5, lac=2, pers=0.5)
        color = [255 if height > 0.5 else 0] * 3
        surf.set_at((x, y), color)


def main():
    # mainloop
    running = __name__ == "__main__"
    while running:
        clock.tick(TARG_FPS)
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
    
        # clearing window
        WIN.fill((255, 192, 143))
    
        WIN.blit(surf, (0, 0))

        # flip the display
        pygame.display.flip()

    pygame.quit()
    sys.exit()


main()