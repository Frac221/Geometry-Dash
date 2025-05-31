import pygame

# Родитель для классов препятствий
class Draw(pygame.sprite.Sprite):
    """класс спрайтов"""

    def __init__(self, image, pos, *groups):
        super().__init__(*groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)

'''
Классы препятствий
'''
class Platform(Draw):
    """ блок"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)

class Spike(Draw):
    """шип"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)

class Coin(Draw):
    """монетка"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)

class Orb(Draw):
    """орб, при нажатии персонаж высоко подпрыгивает"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)

class Trick(Draw):
    """блок, через который можно пройти"""

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)

class End(Draw):
    "зайти, чтобы пройти уровень"

    def __init__(self, image, pos, *groups):
        super().__init__(image, pos, *groups)

