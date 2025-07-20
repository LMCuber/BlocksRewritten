from pyengine.pgbasics import *
#
from .engine import *
from .window import *
from . import fonts


# M I D B L I T  A S S E T S
class MBT(Enum):
    WORKBENCH = auto()


midblits = {
    MBT.WORKBENCH: SurfaceBuilder((400, 200)).fill((20, 40, 89)).set_alpha(80).build()
}


# C L A S S E S
class Midblit:
    def __init__(self, game, window):
        self.game = game
        self.window = window
        self.display = self.window.display
        self.mode = None
    
    @property
    def active(self):
        return self.mode is not None
    
    @property
    def img(self):
        return midblits[self.mode]
    
    def process_event(self, event):
        if self.active:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse = pygame.mouse.get_pos()
                    if not self.rect.collidepoint(mouse):
                        self.set(None)
                    self.game.disable_input = True
            
            elif event.type == pygame.MOUSEMOTION:
                mouses = pygame.mouse.get_pressed()
                if mouses[0]:
                    dx, dy = event.rel
                    m = 0.015
                    self.game.sword.ya -= dx * 0.01
                    self.game.sword.xa += dy * 0.01
            
        if event.type == pygame.MOUSEBUTTONUP:
            # re-enable placing blocks
            self.game.disable_input = False

    def set(self, mode):
        self.mode = mode
        if mode is not None:
            self.rect = self.img.get_rect(center=self.window.center)
    
    def draw(self):
        self.display.blit(self.img, self.rect)
        
        # sword
        if self.mode == MBT.WORKBENCH:
            self.game.sword.update()
            pgb.write(self.display, "center", f"{self.game.sword.num_vertices} vertices", fonts.orbitron[14], BLACK, *self.window.center)
    
    def update(self):
        if self.active:
            self.draw()
            