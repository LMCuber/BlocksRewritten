from pathlib import Path
import pygame


orbitron = [
    pygame.font.Font(Path("res", "fonts", "orbitron", "static", "orbitron-regular.ttf"), i)
    for i in range(1, 101)
]