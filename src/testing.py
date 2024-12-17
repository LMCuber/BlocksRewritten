import pygame


pygame.init()
surf = pygame.Surface((30, 30))
x, y = 400, 400
WIN = pygame.display.set_mode((800, 600), pygame.HWSURFACE)
c = pygame.time.Clock()
font = pygame.font.SysFont("Courier New", 40)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()

    c.tick(1000)
        
    keys = pygame.key.get_pressed()
    m = 3
    if keys[pygame.K_a]:
        x -= m
    if keys[pygame.K_d]:
        x += m
    if keys[pygame.K_w]:
        y -= m
    if keys[pygame.K_s]:
        y += m
    WIN.fill((200, 200, 200))
    WIN.blit(surf, (x, y))

    WIN.blit(font.render(str(int(c.get_fps())), True, (20, 20, 20)), (10, 10))
    pygame.display.flip()
