import pygame
import tomllib as toml
from pathlib import Path
from pyengine.pgshaders import *
from pyengine.pgbasics import *
import pyengine.pgwidgets as pgw
from src.entities import *
from src import fonts


class Game:
    def __init__(self):
        with open(Path("src", "settings.toml"), "rb") as f:
            toml_data = toml.load(f)
            for attr, value in toml_data["game"].items():
                setattr(self, attr, value)
    
    def init_systems(self):
        self.render_system = RenderSystem(self.display)
    
    def create_window(self):
        pygame.display.set_caption("Blockingdom")
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 0)
        self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.WINDOW_CENTER = (self.WINDOW_WIDTH / 2, self.WINDOW_HEIGHT / 2)
        self.display = pygame.display.get_surface()
        self.display.fill((40, 40, 40))
            
    def run(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.running = True
        self.create_window()
        self.init_systems()
        self.shader = ModernglShader(Path("src", "shaders", "vertex.glsl"), Path("src", "shaders", "fragment.glsl"))

        slider = pgw.Slider(self.display, "Slide me!", range(0, 21), 0, pos=(500, 500), width=250, height=80)



        while self.running:
            self.clock.tick()

            for event in pygame.event.get():
                pgw.process_widget_events(event)

                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                
                elif event.type == pygame.VIDEORESIZE:
                    print(event.size)

            self.display.fill((60, 120, 50))

            self.render_system.process()

            write(self.display, "topleft", int(self.clock.get_fps()), fonts.orbitron[20], BLACK, 5, 5)


            # update the pyengine widgets
            pgw.draw_and_update_widgets()

            self.shader.send_surf(0, "tex", self.display)
            self.shader.send_surf(1, "paletteTex", blocks.palette_img)

            # send uniform data to the shader
            self.shader.send("time", ticks())
            self.shader.send("center", self.WINDOW_CENTER)
            self.shader.send("size", (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
            # self.shader.send("rOffset", (-slider.value, 0))
            # self.shader.send("gOffset", (0, 0))
            # self.shader.send("bOffset", (slider.value, 0))
            o = sin(ticks() * 0.001) * -slider.value
            self.shader.send("rOffset", (-o, 0))
            self.shader.send("gOffset", (0, 0))
            self.shader.send("bOffset", (o, 0))

            # render the shader
            self.shader.render()

            pygame.display.flip()

            self.shader.release()


game = Game()
game.run()