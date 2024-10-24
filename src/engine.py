from pathlib import Path
import pygame
from pygame.transform import scale, scale_by


S = 3
BS = 10


def imgload(path, scale=1, frames=1):
    img = pygame.image.load(path)
    if frames == 1:
        return pygame.transform.scale_by(img, scale)
    else:
        imgs = []
        w, h = img.width / frames, img.height
        for x in range(frames):
            imgs.append(pygame.transform.scale_by(img.subsurface(x * w, 0, w, h), scale))
        return imgs