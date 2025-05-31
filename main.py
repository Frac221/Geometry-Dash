import csv
import os
import random
from constants import *
import pygame
from classes import Platform, Spike, Coin, Orb, Trick, End
from pygame.math import Vector2
from pygame.draw import rect

# Инициализация всех модулей Pygame
pygame.init()

# экран 800 на 600
screen = pygame.display.set_mode([800, 600])

# управляет основным игровым циклом во время игры
done = False

# управляет запуском игры в меню
start = False

# устанавливает частоту кадров в программе
clock = pygame.time.Clock()

class Player(pygame.sprite.Sprite):
    """Класс для игрока. Содержит метод обновления, переменные win и die, коллизии и многое другое."""
    win: bool
    died: bool

    def __init__(self, image, platforms, pos, *groups):
        """
        :image: изображение персонажа
        :platforms: группа спрайтов, с которыми игрок может сталкиваться.
        :pos:  начальная позиция (x, y)
        :groups: дополнительные группы спрайтов (например, для отрисовки).
        """
        super().__init__(*groups)
        self.onGround = False  # Игрок на земле?
        self.platforms = platforms  # препятствия
        self.died = False  # флажок смерти игрока?
        self.win = False  # флажок победы игрока?

        self.image = pygame.transform.smoothscale(image, (32, 32)) # изображение персонажа
        self.rect = self.image.get_rect(center=pos)  # хитбокс персонажа
        self.jump_amount = 10  # сила прыжка в пикселях за кадр
        self.particles = []  # трейл за игроком из частиц
        self.isjump = False  # флажок для прыжка персонажа?
        self.vel = Vector2(0, 0)  # скорость начинается с нуля

    def draw_particle_trail(self, x, y, color=(255, 255, 255)):
        """рисует трейл за игроком в случайном месте"""

        self.particles.append(
                [[x - 5, y - 8], [random.randint(0, 25) / 10 - 1, random.choice([0, 0])],
                 random.randint(5, 8)])
        '''Позиция: (x - 5, y - 8) (смещение относительно игрока).
        Скорость: случайная по X (-1.0 до 1.5), 0 по Y.
        Размер: от 5 до 8 пикселей.'''

        '''
        Обновление частиц:
        Перемещение по скорости.
        Уменьшение размера и замедление.
        Отрисовка на поверхности alpha_surf (для эффекта полупрозрачности).
        Удаление частиц с размером ≤ 0.
        '''

        for particle in self.particles:
            particle[0][0] += particle[1][0] # X-позиция + скорость X
            particle[0][1] += particle[1][1] # Y-позиция + скорость Y
            particle[2] -= 0.5 # Уменьшение размера
            particle[1][0] -= 0.4 # Замедление по X
            rect(alpha_surf, color,
                 ([int(particle[0][0]), int(particle[0][1])], [int(particle[2]) for i in range(2)]))
            if particle[2] <= 0:
                self.particles.remove(particle)

    def collide(self, yvel, platforms):
        global coins

        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                """если игрок столкнулся с каким-то препятствием"""
                if isinstance(p, Orb) and (keys[pygame.K_UP] or keys[pygame.K_SPACE]):
                    '''если это орб, то увеличиваем силу прыжка и проигрываем анимацию (круг + гифка).'''
                    pygame.draw.circle(alpha_surf, (255, 255, 0), p.rect.center, 18)
                    screen.blit(pygame.image.load("images/editor-0.9s-47px.gif"), p.rect.center)
                    self.jump_amount = 12  # буст на орбе
                    self.jump()
                    self.jump_amount = 10  # обычный прыжок

                if isinstance(p, End):
                    ''' Если конец, то уровень пройден и обновляем флажок победы'''
                    self.win = True

                if isinstance(p, Spike):
                    '''Если этол шип, то персонаж умирает и обновляется соответсвтующий флажок'''
                    self.died = True
                    coins = 0

                if isinstance(p, Coin):
                    '''Если монетка, то увеличиваем кол-во собранных монеток 
                    и убираем монетку с ее места, обновляя координаты'''

                    coins += 1

                    # убираем монетку
                    p.rect.x = 0
                    p.rect.y = 0

                if isinstance(p, Platform):

                    if yvel > 0:
                        """Приземляется с низу - все хорошо"""
                        self.rect.bottom = p.rect.top  # чтобы персонаж не прошел сквозь блок
                        self.vel.y = 0  # сохраняет скорость, потому что игрок находится на земле

                        # установите для self.onGround значение true, потому что игрок столкнулся с землей
                        self.onGround = True

                        # Сбрасываем прыжок
                        self.isjump = False
                    elif yvel < 0:
                        """если прыгает снизу вверх на блок, то ударяется об него"""
                        self.rect.top = p.rect.bottom  # верх игрока устанавливается в нижней части блока так, как будто он ударяется о него головой
                    else:
                        """если персонаж приземлился с боку на блок, то он умирает"""
                        self.vel.x = 0
                        self.rect.right = p.rect.left  # не дает игроку пройти сквозь стену
                        self.died = True
                        coins = 0

    def jump(self):
        ''' Гравитация (GRAVITY = Vector2(0, 0.8)) постепенно уменьшает эту скорость.'''
        self.vel.y = -self.jump_amount  # Отрицательная скорость = движение вверх

    def update(self):
        if self.isjump:
            if self.onGround:
                """если персонаж хочет прыгнуть и он на земле, то совершаем прыжок"""
                self.jump()

        if not self.onGround:  # если не на земле, то увеличивает гравитацию каждый шаг
            self.vel += GRAVITY

            # максимальная скорость падения
            if self.vel.y > 100: self.vel.y = 100

        # коллизии по x (Проверяет столкновения без движения (yvel = 0))
        self.collide(0, self.platforms)

        # обновляет позицию rect.top на vel.y
        self.rect.top += self.vel.y

        # предполагается, что игрок находится в воздухе, а если нет, то после столкновения он будет перевернут
        self.onGround = False

        # коллизии по y
        self.collide(self.vel.y, self.platforms)

        # проверка состояния, выиграл игрок или нет
        eval_outcome(self.win, self.died)



"""
Функции
"""


def init_level(map):
    """программа просматривает список списков и создает экземпляры определенных препятствий
в зависимости от элемента в списке"""
    x = 0
    y = 0

    for row in map:
        for col in row:

            if col == "0":
                Platform(block, (x, y), elements)

            if col == "Coin":
                Coin(coin, (x, y), elements)

            if col == "Spike":
                Spike(spike, (x, y), elements)
            if col == "Orb":
                orbs.append([x, y])

                Orb(orb, (x, y), elements)

            if col == "T":
                Trick(trick, (x, y), elements)

            if col == "End":
                End(avatar, (x, y), elements)
            x += 32
        y += 32
        x = 0


def blitRotate(surf, image, pos, originpos: tuple, angle: float):
    """
    Поворачивает игрока
    :surf: Поверхность
    :image: Изображение игрока, которое нужно повернуть
    :pos: Текущая позиция изображения игрока
    :originpos: Точка вращения (центр изображения, (16, 16) — половина размера спрайта 32x32).
    :angle: угол вращения
    """
    # вычисляет выровненную по оси ограничивающую рамку повернутого изображения
    w, h = image.get_size()
    box = [Vector2(p) for p in [(0, 0), (w, 0), (w, -h), (0, -h)]] # Углы исходного прямоугольника
    box_rotate = [p.rotate(angle) for p in box] # Поворачиваем каждый угол
    '''
    Лямбды здесь используются для поиска минимальных и максимальных координат повёрнутого прямоугольника.
    Это нужно, чтобы определить новые границы спрайта после вращения.
    '''
    min_box = (min(box_rotate, key=lambda p: p[0])[0], min(box_rotate, key=lambda p: p[1])[1])
    max_box = (max(box_rotate, key=lambda p: p[0])[0], max(box_rotate, key=lambda p: p[1])[1])
    # точка, вокруг которой происходит поворот изображения
    pivot = Vector2(originpos[0], -originpos[1]) # (16, -16) для спрайта 32x32
    pivot_rotate = pivot.rotate(angle)
    pivot_move = pivot_rotate - pivot

    '''
    Найденные min_box и max_box и pivot_move используются для расчёта нового положения спрайта после поворота:
    '''
    origin = (pos[0] - originpos[0] + min_box[0] - pivot_move[0], pos[1] - originpos[1] - max_box[1] + pivot_move[1])

    # получаем повернутое изображение
    rotated_image = pygame.transform.rotozoom(image, angle, 1)

    # поворачиваем и отрисовываем
    surf.blit(rotated_image, origin)


def won_screen():
    """показывает этот экран при прохождении уровня"""
    global attempts, level, fill
    attempts = 0
    player_sprite.clear(player.image, screen) # Очистка спрайтов для визуальной корректности и оптимизации
    screen.fill(pygame.Color("yellow"))
    txt_win1 = f'{coins} / 6 coins'
    txt_win = f"{txt_win1} You beat the level {level + 1}! Press SPACE to restart, or ESC to exit"

    won_game = font.render(txt_win, True, BLUE)

    screen.blit(won_game, (200, 300))
    level += 1

    wait_for_key()
    reset()


def death_screen():
    """Показывает экран смерти"""
    global attempts, fill
    fill = 0
    player_sprite.clear(player.image, screen) # Очистка спрайтов для визуальной корректности и оптимизации
    attempts += 1
    game_over = font.render("Game Over. [SPACE] to restart", True, WHITE)

    screen.fill(pygame.Color("sienna1"))
    screen.blits([[game_over, (100, 100)], [tip, (100, 400)]])

    wait_for_key()
    reset()


def eval_outcome(won: bool, died: bool):
    if won:
        won_screen()
    if died:
        death_screen()


def block_map(level_num):
    """
    :type level_num: rect(screen, BLACK, (0, 0, 32, 32))
    открывает csv-файл, содержащий нужную карту уровней
    """
    lvl = []
    with open(level_num, newline='') as csvfile:
        trash = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in trash:
            lvl.append(row)
    return lvl


def start_screen():
    """основное меню. возможность переключения уровня, руководство по управлению и обзор игры."""
    global level
    if not start:
        screen.fill(BLACK)
        if pygame.key.get_pressed()[pygame.K_1]:
            level = 0
        if pygame.key.get_pressed()[pygame.K_2]:
            level = 1

        welcome = font.render(f"Welcome to Pydash. choose level({level + 1}) by keypad", True, WHITE)

        controls = font.render("Controls: jump: Space/Up exit: Esc", True, GREEN)

        screen.blits([[welcome, (100, 100)], [controls, (100, 400)], [tip, (100, 500)]])

        level_memo = font.render(f"Level {level + 1}.", True, (255, 255, 0))
        screen.blit(level_memo, (100, 200))


def reset():
    """сбрасывает группы спрайтов, музыку и т.д. для смерти и нового уровня"""
    global player, elements, player_sprite, level

    if level == 1:
        pygame.mixer.music.load(os.path.join("music", "base_after_base.mp3"))
    pygame.mixer_music.play()
    player_sprite = pygame.sprite.Group()
    elements = pygame.sprite.Group()
    player = Player(avatar, elements, (150, 150), player_sprite)
    init_level(
            block_map(
                    level_num=levels[level]))


def move_map():
    """перемещает препятствия по экрану"""
    for sprite in elements:
        sprite.rect.x -= CameraX


def draw_stats(surf, money=0):
    """
    Рисует статистику игрока на указанной поверхности.

    Параметры:
        surf (Surface): Поверхность для отрисовки (обычно экран)
        money (int): Количество собранных монет
    """
    global fill

    # 1. Подготовка цветов для прогресс-бара
    progress_colors = [
        pygame.Color("red"),  # 0-25%
        pygame.Color("orange"),  # 25-50%
        pygame.Color("yellow"),  # 50-75%
        pygame.Color("lightgreen"),  # 75-90%
        pygame.Color("green")  # 90-100%
    ]

    # 2. Отрисовка счетчика попыток
    tries = font.render(f" Attempt {str(attempts)}", True, WHITE)

    # 3. Отрисовка монет
    BAR_LENGTH = 600  # Длина прогресс-бара
    BAR_HEIGHT = 10  # Высота прогресс-бара

    for i in range(1, money):
        screen.blit(coin, (BAR_LENGTH, 25))

    # 4. Обновление прогресс-бара
    fill += 0.5  # Плавное заполнение

    # 5. Создание прямоугольников для прогресс-бара
    outline_rect = pygame.Rect(0, 0, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(0, 0, fill, BAR_HEIGHT)

    # 6. Выбор цвета в зависимости от заполненности
    col = progress_colors[int(fill / 100)]

    # 7. Отрисовка прогресс-бара
    rect(surf, col, fill_rect, 0, 4)  # Заливка
    rect(surf, WHITE, outline_rect, 3, 4)  # Контур

    # 8. Вывод статистики на экран
    screen.blit(tries, (BAR_LENGTH, 0))


def wait_for_key():
    """отдельный игровой цикл для ожидания нажатия клавиши во время выполнения игрового цикла
    """
    global level, start
    waiting = True
    while waiting:
        clock.tick(60)
        pygame.display.flip()

        if not start:
            start_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    start = True
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()



def resize(img, size=(32, 32)):
    resized = pygame.transform.smoothscale(img, size)
    return resized


"""
Глобальные переменные
"""
font = pygame.font.SysFont("lucidaconsole", 20)

# квадратная грань блока является главным символом, а значок окна - гранью блока
avatar = pygame.image.load(os.path.join("images", "avatar.png"))  # load the main character
pygame.display.set_icon(avatar)
#  эта поверхность имеет альфа-значение для цветов, поэтому след игрока будет исчезать при использовании непрозрачности
alpha_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

# группы спрайтов
player_sprite = pygame.sprite.Group()
elements = pygame.sprite.Group()

# картинки
spike = pygame.image.load(os.path.join("images", "obj-spike.png"))
spike = resize(spike)
coin = pygame.image.load(os.path.join("images", "coin.png"))
coin = pygame.transform.smoothscale(coin, (32, 32))
block = pygame.image.load(os.path.join("images", "YosXCdCJ6nM.jpg"))
block = pygame.transform.smoothscale(block, (32, 32))
orb = pygame.image.load((os.path.join("images", "orb-yellow.png")))
orb = pygame.transform.smoothscale(orb, (32, 32))
trick = pygame.image.load((os.path.join("images", "obj-breakable.png")))
trick = pygame.transform.smoothscale(trick, (32, 32))

#  ints
fill = 0
num = 0
CameraX = 0
attempts = 0
coins = 0
angle = 0
level = 0

# list
particles = []
orbs = []
win_cubes = []

# инициализация уровней с помощью
levels = ["level_1.csv", "level_2.csv"]
level_list = block_map(levels[level])
level_width = (len(level_list[0]) * 32)
level_height = len(level_list) * 32
init_level(level_list)

# Название окна для игры
pygame.display.set_caption('Geometry Dash')

#
text = font.render('image', False, (255, 255, 0))

# музыка в меню
music = pygame.mixer_music.load(os.path.join("music", "stereo_madness.mp3"))
# pygame.mixer_music.play()

# задний фон
bg = pygame.image.load(os.path.join("images", "bg.png"))

# экземпляр класса Player
player = Player(avatar, elements, (150, 150), player_sprite)

# Подсказка
tip = font.render('Для прохождения необходимо собрать как можно больше монет', True, BLUE)

while not done:
    keys = pygame.key.get_pressed()

    if not start:
        wait_for_key()
        reset()

        start = True

    player.vel.x = 6

    eval_outcome(player.win, player.died)
    if keys[pygame.K_UP] or keys[pygame.K_SPACE]:
        player.isjump = True

    # Reduce the alpha of all pixels on this surface each frame.
    # Control the fade2 speed with the alpha value.

    alpha_surf.fill((255, 255, 255, 1), special_flags=pygame.BLEND_RGBA_MULT)

    player_sprite.update()
    CameraX = player.vel.x  # для препятствий
    move_map()  # движение камеры на элементы

    screen.blit(bg, (0, 0)) #очистка экрана с задним фоном

    player.draw_particle_trail(player.rect.left - 1, player.rect.bottom + 2,
                               WHITE)
    screen.blit(alpha_surf, (0, 0))  # Вывод alpha_surf на экран.
    draw_stats(screen, coins)

    if player.isjump:
        """поворачивает игрока, когда он прыгает"""
        angle -= 8.1712  # это угол, необходимый для поворота на 360 градусов на длину, пройденную игроком за один прыжок
        blitRotate(screen, player.image, player.rect.center, (16, 16), angle)
    else:
        """если не прыгает, то просто отрисовать"""
        player_sprite.draw(screen)  # спрайт игрока
    elements.draw(screen)  # рисует препятствия

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                """выход"""
                done = True
            if event.key == pygame.K_2:
                """меняется уровень"""
                player.jump_amount += 1

            if event.key == pygame.K_1:
                """меняется уровень """

                player.jump_amount -= 1

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
