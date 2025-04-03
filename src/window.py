import pygame
from pathlib import Path
import tomllib as toml
from pyengine.pgbasics import set_pyengine_hwaccel


pygame.init()


class Window:
    def create_window(self, width, height, vsync, fps_cap):
        # set PyEngine hwaccel flag
        set_pyengine_hwaccel(False)
        # pygame window and OpenGL flags
        pygame.display.set_caption("Blockingdom")
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, vsync)
        # window parameters
        self.width = width
        self.height = height
        self.size = (self.width, self.height)
        self.vsync = vsync
        self.fps_cap = fps_cap
        self.center = (self.width / 2, self.height / 2)
        self.window = pygame.display.set_mode((self.width, self.height), 
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE,
            vsync=self.vsync
        )
        self.display = pygame.display.get_surface()


window = Window()
with open(Path("settings.toml"), "rb") as f:
    toml_data = toml.load(f)
    window.create_window(**toml_data["window"])
