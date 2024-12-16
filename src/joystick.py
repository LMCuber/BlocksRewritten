import pygame


class JoystickManager:
    def __init__(self):
        if pygame.joystick.get_count() > 0:
            self.joysticks = [pygame.joystick.Joystick(n) for n in range(pygame.joystick.get_count())]
        else:
            self.joysticks = []
        
    def update(self):
        for joy in self.joysticks:
            pass