import pygame
from pathlib import Path
import tomllib as toml


pygame.init()


class Window:
    def create_window(self, width, height, vsync, target_fps):
        pygame.display.set_caption("Blockingdom")
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, vsync)
        self.width = width
        self.height = height
        self.vsync = vsync
        self.target_fps = target_fps
        self.center = (self.width / 2, self.height / 2)
        self.window = pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE, vsync=self.vsync)
        self.display = pygame.display.get_surface()


window = Window()
with open(Path("src", "settings.toml"), "rb") as f:
    toml_data = toml.load(f)
    window.create_window(**toml_data["window"])
