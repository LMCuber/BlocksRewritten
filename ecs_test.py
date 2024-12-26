import pygame


pygame.init()

WIN = pygame.display.set_mode((400, 300))

font = pygame.font.SysFont("Courier New", 40)
clock = pygame.time.Clock()

while True:
    clock.tick(165)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()

    surf = font.render(str(int(clock.get_fps())), True, (120, 3, 40))
    WIN.fill((40, 245, 234))
    WIN.blit(surf, (5, 5))
    pygame.display.flip()

