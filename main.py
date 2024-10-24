import pygame
import tomllib as toml
from pathlib import Path
from pyengine.pgshaders import *
from pyengine.pgbasics import *
from src.entities import *


class Game:
    def __init__(self):
        with open(Path("res", "settings.toml"), "rb") as f:
            toml_data = toml.load(f)
            for attr, value in toml_data["game"].items():
                setattr(self, attr, value)
    
    def init_systems(self):
        # render_system = RenderSystem()
        return
    
    def create_window(self):
        pygame.display.set_caption("Blockingdom")
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
        self.display = pygame.display.get_surface()
        self.display.fill((40, 40, 40))
            
    def fill_bg(self):
        self.display.fill((80, 80, 80))

    def run(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.running = True
        self.create_window()
        self.init_systems()
        self.shader = ModernglShader(Path("src", "shaders", "vertex.glsl"), Path("src", "shaders", "fragment.glsl"))
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            self.fill_bg()

            self.shader.send_surf(self.display)
            self.shader.send("time", ticks())
            self.shader.render()

            pygame.display.flip()

            self.shader.release()

            self.clock.tick(60)


game = Game()
game.run()