from pyengine.ecs import *
import random
import math
import esper
import time
import cProfile


pygame.init()
esper_mode = False


WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Courier New", 26)


@dataclass
class Transform:
    x: float
    y: float
    xvel: float
    yvel: float


class Sprite:
    def __init__(self):
        self.image = pygame.Surface((30, 30))
        self.image.fill([random.randint(0, 255) for _ in range(3)])


if not esper_mode:
    Transform = component(Transform)
    Sprite = component(Sprite)


class RenderSystem:
    def __init__(self, display):
        self.display = display
        if not esper_mode:
            self.set_cache(True)
    
    def process(self):
        global num_iter
        num_iter += 1
        self.display.fill((170, 170, 170))
        for ent, (spr, tr) in (self.get_components(chunks=(0,)) if not esper_mode else esper.get_components(Sprite, Transform)):
            tr.x += tr.xvel
            tr.y += tr.yvel
            if tr.x + spr.image.width >= WIDTH or tr.x <= 0:
                tr.xvel *= -1 
            if tr.y + spr.image.height >= HEIGHT or tr.y <= 40:
                tr.yvel *= -1
            self.display.blit(spr.image, (tr.x, tr.y))
        self.display.blit(font.render(f"{int(clock.get_fps())}\n{num_entities} ent.\nmode: {'prop' if not esper_mode else 'esper'}", True, (0, 0, 0)), (5, 5))


if not esper_mode:
    RenderSystem = system(Sprite, Transform)(RenderSystem)

render_system = RenderSystem(WIN)
if esper_mode:
    esper.add_processor(render_system)


num_entities = 10 ** 4
for _ in range(num_entities):
    angle = random.uniform(0, 2 * math.pi)
    radius = 3
    if esper_mode:
        esper.create_entity(
            Sprite(),
            Transform(WIDTH / 2, HEIGHT / 2, math.cos(angle) * radius, math.sin(angle) * radius),
        )
    else:
        create_entity(
            Sprite(),
            Transform(WIDTH / 2, HEIGHT / 2, math.cos(angle) * radius, math.sin(angle) * radius),
            chunk=0
        )


num_iter = 0


def main():
    last = time.time()
    start = time.time()

    while True:
        clock.tick(165)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit()
        
        render_system.process()
        # if esper_mode:
        #     esper.process()

        if time.time() - last >= 1:
            print(int(clock.get_fps()), end=", ")
            last = time.time()
        if time.time() - start >= 5:
            pass
    
        if num_iter >= 500:
            exit()
        
        pygame.display.flip()


cProfile.run("main()", sort="cumtime")
