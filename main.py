# период неуязаимости
# пули врагов
import os
import datetime

import pygame
from math import sqrt, atan, pi
import sqlite3
from random import randint, choice


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Cur(pygame.sprite.Sprite):
    def __init__(self, *group):
        super().__init__(*group)
        self.image = load_image("cur_2.png", -1)
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0

    def update(self, x, y):
        self.rect.x, self.rect.y = x, y


class Picture(pygame.sprite.Sprite):
    def __init__(self, picture):
        super().__init__()
        self.image = load_image(picture)
        self.rect = self.image.get_rect()
        self.start_w = self.rect.width
        self.rect.x = 0
        self.rect.y = 0


class Loading(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.images = [load_image("loading1.png"), load_image("loading2.png"), load_image("loading3.png"),
                       load_image("loading4.png"), load_image("loading5.png"), load_image("loading6.png"),
                       load_image("loading7.png"), load_image("loading8.png"), load_image("loading9.png"),
                       load_image("loading10.png"), load_image("loading11.png"), load_image("loading12.png"),
                       load_image("loading13.png"), load_image("loading14.png"), load_image("loading15.png"),
                       load_image("loading16.png")]
        self.cur = 0
        self.image = self.images[self.cur]
        self.rect = self.image.get_rect()
        self.start_w = self.rect.width
        self.rect.x = x
        self.rect.y = y
        self.load_sprites = pygame.sprite.Group()

    def update(self):
        self.cur += 1
        self.image = self.images[self.cur % 16]


class HpBar(pygame.sprite.Sprite):
    def __init__(self, x, y, type, *group):
        super().__init__(*group)
        if type == 'left':
            self.image = load_image("hp.png")
        else:
            self.image = load_image("hp_2.png")
        self.rect = self.image.get_rect()
        self.start_w = self.rect.width
        self.rect.x = x
        self.rect.y = y


class Bullet(pygame.sprite.Sprite):
    def __init__(self, id, x, y, speed, speed_x, speed_y, author, rotate=0):
        # range
        self.id = id
        self.x = x
        self.y = y
        self.speed = speed
        self.speed_x, self.speed_y = speed_x, speed_y
        self.author = author
        self.frames = []
        self.rotate = rotate
        self.cur_frame = 0

        if id == 5:
            self.cut_sheet(load_image(f"bullet_{id}.png"), 20, 1)
            self.cur_frame = 0
            self.image0 = self.frames[self.cur_frame]
            self.image = pygame.transform.rotate(self.image0, rotate)
            self.rect = self.rect.move(x, y)
        elif id == 11:
            self.cut_sheet(load_image(f"bullet_{id}.png"), 16, 1)
            self.cur_frame = 0
            self.image0 = self.frames[self.cur_frame]
            self.image = pygame.transform.rotate(self.image0, rotate)
            self.rect = self.rect.move(x, y)
        else:
            self.image = pygame.transform.rotate(load_image(f"bullet_{id}.png"), rotate)
            self.rect = self.image.get_rect()
        if self.speed_x < 0:
            self.image = pygame.transform.flip(self.image, True, True)
            self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = self.x
        self.rect.y = self.y
        self.mask = pygame.mask.from_surface(self.image)

        self.width = self.rect.width
        self.height = self.rect.height
        self.timer = 0

        super().__init__()

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                    sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.extend([sheet.subsurface(pygame.Rect(
                frame_location, self.rect.size))]*7)

    def update(self, room):
        self.timer += 1

        self.x += self.speed_x
        self.y += self.speed_y
        self.rect.update(self.x, self.y, self.rect.width, self.rect.height)
        if self.id == 2 and self.timer >= 10:
            self.timer = 0
            self.image = pygame.transform.rotate(self.image, 90)
            self.mask = pygame.mask.from_surface(self.image)
        if self.id == 5 or self.id == 11:
            self.cur_frame = (self.cur_frame + 1)
            if self.cur_frame < len(self.frames):
                self.image = self.frames[self.cur_frame]
                self.image = pygame.transform.rotate(self.image, self.rotate)
                self.mask = pygame.mask.from_surface(self.image)
            else:
                self.id = 10
                self.speed_x = 10**5
                self.speed_y = 10**5

        for spr in pygame.sprite.spritecollide(self, room.all_decorations_sprites, False):
            if pygame.sprite.collide_mask(self, spr) and spr.is_penetrable == False:
                room.all_bullets_sprites.remove(self)
                if self in room.bullets:
                    del room.bullets[room.bullets.index(self)]


class Weapon(pygame.sprite.Sprite):
    def __init__(self, id, x, y, type, speed, attack, bullet_id, k_x, k_y, k_x_rev, p):
        # range
        self.id = id
        self.x = x
        self.y = y
        self.attack = attack
        self.bullet_id = bullet_id
        self.k_x0 = k_x
        self.k_y0 = k_y
        self.k_x = k_x
        self.k_y = k_y
        self.k_x_rev = k_x_rev
        self.speed_x = 1
        self.speed_y = 1
        self.type_attack = type
        self.speed = speed
        self.attack = attack
        self.rotated_x = False
        self.frames = []

        self.cut_sheet(load_image(f"weapon_{id}.png"), 9, 1)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
        self.mask = pygame.mask.from_surface(self.image)
        self.p = p
        self.processes = {'attack': -1}
        self.width = self.rect.width
        self.height = self.rect.height
        self.timer = 0

        super().__init__()

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                    sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.extend([sheet.subsurface(pygame.Rect(
                frame_location, self.rect.size))] * int(self.speed))

    def update(self):
        if self.rotated_x:
            self.x, self.y = self.p.x + self.k_x_rev + self.p.width//2 - self.width//2, \
                         self.p.y + self.k_y + self.p.height//2 - self.height//2
        else:
            self.x, self.y = self.p.x + self.k_x + self.p.width // 2 - self.width // 2, \
                             self.p.y + self.k_y + self.p.height // 2 - self.height // 2
        self.image = self.frames[0]
        if self.rotated_x:
            self.image = pygame.transform.flip(self.image, True, False)
            self.mask = pygame.mask.from_surface(self.image)

        self.rect.update(self.x, self.y, self.rect.width, self.rect.height)

        if self.processes['attack'] != -1:
            if self.processes['attack'] < len(self.frames):
                self.cur_frame = (self.cur_frame + 1) % len(self.frames)
                self.image = self.frames[self.cur_frame]
                if self.rotated_x:
                    self.image = pygame.transform.flip(self.image, True, False)
                self.mask = pygame.mask.from_surface(self.image)
                self.processes['attack'] += 1
            else:
                self.processes['attack'] = -1


class Boss(pygame.sprite.Sprite):
    def __init__(self, id, x, y, health_points, attack, speed, radius1, radius2,
                 type_attack, bullet_id, run_pos, attack1_pos, attack2_pos, death_pos, run_moment, attack1_moment1,
                 attack1_moment2, attack2_moment1, attack2_moment2, end_of_run, end_of_attack1, end_of_attack2,
                end_of_death, rows, columns, surface):
        self.health_points = health_points
        self.start_health_points = health_points
        self.attack = attack
        self.radius1 = radius1
        self.radius2 = radius2
        self.type_attack = type_attack
        self.bullet_id = bullet_id
        self.id = id
        self.x = x
        self.y = y
        self.invulnerability = 0
        self.speed = speed
        self.run_pos = run_pos
        self.attack1_pos = attack1_pos
        self.attack2_pos = attack2_pos
        self.death_pos = death_pos
        self.run_moment = run_moment
        self.attack1_moment1 = attack1_moment1
        self.attack1_moment2 = attack1_moment2
        self.attack2_moment1 = attack2_moment1
        self.attack2_moment2 = attack2_moment2
        self.rotate_x = False
        ##
        self.fast = 10
        ##
        self.end_of_run = end_of_run
        self.end_of_attack1 = end_of_attack1
        self.end_of_attack2 = end_of_attack2
        self.end_of_death = end_of_death

        self.frames = []
        self.cut_sheet(surface, columns, rows)
        self.image = self.frames[0][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.rect.move(self.x, self.y)

        self.frames[run_pos] = self.frames[run_pos][:(end_of_run + 1) * self.fast]
        self.frames[attack1_pos] = self.frames[attack1_pos][:(end_of_attack1 + 1) * self.fast]
        if attack2_pos:
            self.frames[attack2_pos] = self.frames[attack2_pos][:(end_of_attack2 + 1) * self.fast]
        self.frames[death_pos] = self.frames[death_pos][:(end_of_death + 1) * self.fast]

        self.processes = {'walking': -1, 'attack': -1, 'death': -1}
        self.processes_sprites = [self.frames[run_pos], self.frames[attack1_pos],
                                  self.frames[death_pos]]

        self.width = self.rect.width
        self.height = self.rect.height
        self.timer = 0
        self.timer2 = 0
        self.target = ()
        self.key = 0
        self.save_pos = ()

        super().__init__()

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            s = []
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                s.extend([sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size))] * self.fast)
            self.frames.append(s)

    def update(self, i, speed_x=0, speed_y=0):
        if not (i == 0 and speed_x == 0 and speed_y == 0 and self.id == 0):
            self.image = self.processes_sprites[i][
                (list(self.processes.values())[i] - 1) % len(self.processes_sprites[i])]
        else:
            self.image = self.processes_sprites[i][1*self.fast]
        if self.rotate_x:
            self.image = pygame.transform.flip(self.image, True, False)
        self.mask = pygame.mask.from_surface(self.image)

        if i == 0:
            self.x += speed_x
            self.y += speed_y
            self.rect.update(self.x, self.y, self.rect.width, self.rect.height)


class Creatures(pygame.sprite.Sprite):
    def __init__(self, id, x, y, health_points, attack, speed, radius1, radius2,
                 type_attack, bullet_id, run_pos, attack1_pos, attack2_pos, death_pos, run_moment, attack1_moment1,
                 attack1_moment2, attack2_moment1, attack2_moment2, end_of_run, end_of_attack1, end_of_attack2,
                end_of_death, rows, columns, surface, weapon=None):
        self.health_points = health_points
        self.start_health_points = health_points
        self.attack = attack
        self.radius1 = radius1
        self.radius2 = radius2
        self.type_attack = type_attack
        self.bullet_id = bullet_id
        self.id = id
        self.x = x
        self.y = y
        self.invulnerability = 0
        self.speed = speed
        self.start_speed = speed
        self.run_pos = run_pos
        self.attack1_pos = attack1_pos
        self.attack2_pos = attack2_pos
        self.death_pos = death_pos
        self.run_moment = run_moment
        self.attack1_moment1 = attack1_moment1
        self.attack1_moment2 = attack1_moment2
        self.attack2_moment1 = attack2_moment1
        self.attack2_moment2 = attack2_moment2
        self.rotate_x = False
        self.weapon = weapon
        ##
        self.fast = 10
        ##
        self.end_of_run = end_of_run
        self.end_of_attack1 = end_of_attack1
        self.end_of_attack2 = end_of_attack2
        self.end_of_death = end_of_death

        self.frames = []
        self.cut_sheet(surface, columns, rows)
        self.image = self.frames[0][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.rect.move(self.x, self.y)

        self.frames[run_pos] = self.frames[run_pos][:(end_of_run + 1) * self.fast]
        self.frames[attack1_pos] = self.frames[attack1_pos][:(end_of_attack1 + 1) * self.fast]
        if attack2_pos:
            self.frames[attack2_pos] = self.frames[attack2_pos][:(end_of_attack2 + 1) * self.fast]
        self.frames[death_pos] = self.frames[death_pos][:(end_of_death + 1) * self.fast]

        self.processes = {'walking': -1, 'attack': -1, 'death': -1}
        self.processes_sprites = [self.frames[run_pos], self.frames[attack1_pos],
                                  self.frames[death_pos]]

        self.width = self.rect.width
        self.height = self.rect.height
        self.timer = 0
        self.timer2 = 0
        self.target = ()
        self.key = 0
        self.save_pos = ()

        super().__init__()

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            s = []
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                s.extend([sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size))] * self.fast)
            self.frames.append(s)

    def update(self, i, speed_x=0, speed_y=0):
        if not (i == 0 and speed_x == 0 and speed_y == 0 and self.id == 0):
            self.image = self.processes_sprites[i][
                (list(self.processes.values())[i] - 1) % len(self.processes_sprites[i])]
        else:
            self.image = self.processes_sprites[i][1*self.fast]
        if self.rotate_x:
            self.image = pygame.transform.flip(self.image, True, False)
        self.mask = pygame.mask.from_surface(self.image)

        if i == 0:
            self.x += speed_x
            self.y += speed_y
            self.rect.update(self.x, self.y, self.rect.width, self.rect.height)


class Decoration(pygame.sprite.Sprite):
    def __init__(self, id, x, y, health_points, is_penetrable, is_passable):
        if health_points is not None:
            self.health_points = int(health_points)
        else:
            self.health_points = 10 ** 9
        self.is_penetrable = is_penetrable
        self.is_passable = is_passable
        self.id = id
        self.x = x
        self.y = y
        self.speed = 0
        self.processes = {'stand': 0}
        self.processes_sprites = {'stand': f'3_{id}.png'}
        super().__init__()
        self.image = load_image({'stand': f'3_{id}.png'}['stand'])
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
        self.width = self.rect.width
        self.height = self.rect.height
        self.mask = pygame.mask.from_surface(self.image)


class Room:
    def __init__(self, x, y, room_type, game):
        self.x = x
        self.y = y
        self.type = room_type
        self.game = game
        self.enemies = [self.game.p]
        self.bullets = []
        self.decorations = []
        self.is_visited = False
        self.all_bullets_sprites = pygame.sprite.Group()
        self.all_decorations_sprites = pygame.sprite.Group()
        self.all_monsters_sprites = pygame.sprite.Group()
        self.all_weapons_sprites = pygame.sprite.Group()

    def generation(self, is_boss_room):
        #оружие
        self.all_weapons_sprites.add(self.game.p.weapon)
        # генерация декораций
        for i in range(2, 12):
            for j in range(20):
                # сама клетка
                new_id = choice([3] * 24 + [4] * 3 + [5] * 3 + [6])
                d = Decoration(new_id, j * 96, i * 96, *self.game.DECORATIONS_DATA[new_id - 1][1:])
                self.all_decorations_sprites.add(d)
                self.decorations.append(d)
                # cундук на ней
                if 1 == randint(1, self.game.CHANCE_OF_CHEST[1]) and i != 11:
                    c = Decoration(self.game.DECORATIONS_DATA[0][0], j * 96, i * 96, *self.game.DECORATIONS_DATA[0][1:])
                    self.all_decorations_sprites.add(c)
                    self.decorations.append(c)
                if not is_boss_room:
                    # моб на ней
                    if 1 == randint(1, self.game.CHANCE_OF_MOB[1]) and i not in (2, 10, 11) and j not in (0, 1, 18, 19):
                        mob = list(choice(self.game.MONSTERS_DATA))
                        while not ((self.game.LEVEL == 1 and 1 <= mob[0] <= 5) or
                                   (self.game.LEVEL == 2 and 7 <= mob[0] <= 12) or
                                   (self.game.LEVEL == 3 and 13 <= mob[0] <= 17)):
                            mob = list(choice(self.game.MONSTERS_DATA))
                        e = Creatures(mob[0], j * 96, i * 96, *mob[1:], load_image(f"monster_{mob[0]}.png"))
                        self.all_monsters_sprites.add(e)
                        self.enemies.append(e)
                        if e.id == 13:
                            k1, k2 = 1, 1
                            if j > 9:
                                k1 = -1
                            if i > 6:
                                k2 = -1
                            e2 = Creatures(mob[0], (j + k1) * 96, i * 96, *mob[1:], load_image(f"monster_{mob[0]}.png"))
                            self.all_monsters_sprites.add(e2)
                            self.enemies.append(e2)
                            e3 = Creatures(mob[0], j * 96, (i + k2) * 96, *mob[1:], load_image(f"monster_{mob[0]}.png"))
                            self.all_monsters_sprites.add(e3)
                            self.enemies.append(e3)
                            e4 = Creatures(mob[0], (j + k1) * 96, (i + k2) * 96, *mob[1:],
                                          load_image(f"monster_{mob[0]}.png"))
                            self.all_monsters_sprites.add(e4)
                            self.enemies.append(e4)
                        elif e.id == 14:
                            k1, k2 = 1, 1
                            if j > 9:
                                k1 = -1
                            if i > 6:
                                k2 = -1
                            e2 = Creatures(mob[0], (j + k1 * 0.5) * 96, (i + k2) * 96, *mob[1:],
                                           load_image(f"monster_{mob[0]}.png"))
                            self.all_monsters_sprites.add(e2)
                            self.enemies.append(e2)
                            e3 = Creatures(mob[0], (j - k1 * 0.5) * 96, (i + k2) * 96, *mob[1:],
                                           load_image(f"monster_{mob[0]}.png"))
                            self.all_monsters_sprites.add(e3)
                            self.enemies.append(e3)

        if is_boss_room:
            id = self.game.LEVEL - 1
            boss = self.game.BOSSES_DATA[id]
            b = Boss(boss[0], 10 * 96, 5 * 96, *boss[1:],
                                       load_image(f"boss_{boss[0]}.png"))
            self.all_monsters_sprites.add(b)
            self.enemies.append(b)

        # стена
        w = Decoration(2, 0, 0, *self.game.DECORATIONS_DATA[1][1:])
        self.all_decorations_sprites.add(w)
        self.decorations.append(w)

        self.all_monsters_sprites.add(self.enemies[0])

    def add_doors(self):
        # двери
        self.doors = {'door1': None, 'door2': None, 'door3': None, 'door4': None}
        if self.game.room_y - 1 >= 0:
            if self.game.map[self.game.room_y - 1][self.game.room_x].type != -1:
                d1 = Decoration(7, 864, 0, *self.game.DECORATIONS_DATA[6][1:])
                self.all_decorations_sprites.add(d1)
                self.decorations.append(d1)
                self.doors['door1'] = d1

        if self.game.room_y + 1 < self.game.map_size:
            if self.game.map[self.game.room_y + 1][self.game.room_x].type != -1:
                d2 = Decoration(8, 864, 1062, *self.game.DECORATIONS_DATA[7][1:])
                self.all_decorations_sprites.add(d2)
                self.decorations.append(d2)
                self.doors['door2'] = d2

        if self.game.room_x - 1 >= 0:
            if self.game.map[self.game.room_y][self.game.room_x - 1].type != -1:
                d3 = Decoration(9, 0, 444, *self.game.DECORATIONS_DATA[8][1:])
                self.all_decorations_sprites.add(d3)
                self.decorations.append(d3)
                self.doors['door3'] = d3

        if self.game.room_x + 1 < self.game.map_size:
            if self.game.map[self.game.room_y][self.game.room_x + 1].type != -1:
                d4 = Decoration(10, 1902, 444, *self.game.DECORATIONS_DATA[9][1:])
                self.all_decorations_sprites.add(d4)
                self.decorations.append(d4)
                self.doors['door4'] = d4

    def __str__(self):
        if self.type != -1:
            return str(self.type)
        else:
            return ' '


class GameOverWindow:
    def __init__(self, width, height, fps, screen, stat):
        self.SIZE = self.WIDTH, self.HEIGHT = width, height
        self.screen = screen
        self.FPS = fps
        self.STAT = stat
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.running = True
        self.all_sprites = pygame.sprite.Group()
        self.main_picture = Picture('game-over1.png')
        self.main_picture2 = Picture('game-over2.png')
        self.main_picture.rect.x = -1920 // 2
        self.main_picture2.rect.x = 1920
        self.all_sprites.add(self.main_picture)
        self.all_sprites.add(self.main_picture2)
        self.key = 0
        self.begin()

    def begin(self):
        while self.running:
            self.all_sprites.draw(self.screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            if self.main_picture.rect.x < 0:
                self.main_picture.rect.x += 5
                self.main_picture2.rect.x -= 5

            if any(pygame.key.get_pressed()) and self.key == 1:
                self.key = 2
                self.main_picture = Picture('game-over5.png')
                self.all_sprites = pygame.sprite.Group(self.main_picture)

            if self.key >= 2:
                self.key += 1

                text1 = pygame.font.Font('data/front.otf', 48).render(f"Убито монстров * {self.STAT['kill']-1}", False,
                                                                (180, 60, 60))
                self.screen.blit(text1, (600, 100))

                text2 = pygame.font.Font('data/front.otf', 48).render(f"Убито боссов * {self.STAT['boss_kill']}", False,
                                                                (180, 60, 60))
                self.screen.blit(text2, (650, 250))

                text3 = pygame.font.Font('data/front.otf', 48).render(f"Комнат посещенно * {self.STAT['room']}", False,
                                                                (60, 180, 60))
                self.screen.blit(text3, (550, 400))

                text4 = pygame.font.Font('data/front.otf', 48).render(f"Этажей посещенно * {self.STAT['loops']+1}",
                                                                      False, (60, 180, 60))
                self.screen.blit(text4, (550, 550))

                text5 = pygame.font.Font('data/front.otf', 48).render(f"Нанесено урона * {self.STAT['dmg']}", False,
                                                                (60, 60, 180))
                self.screen.blit(text5, (600, 700))

                text6 = pygame.font.Font('data/front.otf', 48).render(f"Времени проведенно * "
                                                                 f"{str(self.STAT['time']).split('.')[0]}", False,
                                                                 (60, 60, 180))
                self.screen.blit(text6, (450, 850))

                if self.STAT['win_game']:
                    text7 = pygame.font.Font('data/front.otf', 48).render(f"Поздравляем, вы прошли игру", False,
                                                                      (50, 220, 50))
                    self.screen.blit(text7, (420, 1000))
                pygame.display.update()

            if any(pygame.key.get_pressed()) and self.key >= 30:
                m = MainWindow()
                self.running = False

            if not self.main_picture.rect.x < 0 and self.key == 0:
                self.main_picture = Picture('game-over.png')
                self.all_sprites = pygame.sprite.Group(self.main_picture)
                self.key = 1

            pygame.display.flip()
            self.clock.tick(self.FPS)


class GameWindow:
    def __init__(self, width, height, fps, screen):
        self.SIZE = self.WIDTH, self.HEIGHT = width, height
        self.screen = screen
        self.map_size = 9
        self.LOADING = pygame.sprite.GroupSingle(Loading(430, 910))
        self.LOADING.draw(self.screen)
        self.FPS = fps
        self.running = True
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.t = datetime.datetime.now()

        self.STAT = {'kill':0, 'boss_kill':0, 'room':0, 'loops':0, 'dmg':0, 'time':0, 'win_game': False}

        self.DB = 'Database.db'

        # получение информации о всех монстрах, пулях и декорациях
        con = sqlite3.connect(self.DB)
        cur = con.cursor()
        self.MONSTERS_DATA = cur.execute("""SELECT * FROM mobs""").fetchall()
        self.BULLETS_DATA = cur.execute("""SELECT * FROM bullets""").fetchall()
        self.DECORATIONS_DATA = cur.execute("""SELECT * FROM decorations""").fetchall()
        self.BOSSES_DATA = cur.execute("""SELECT * FROM bosses""").fetchall()
        self.WEAPONS_DATA = cur.execute("""SELECT * FROM weapons""").fetchall()
        con.close()

        self.start1()
        self.generation()

    def start1(self):
        self.CHANCE_OF_MOB = (1, 30)
        self.CHANCE_OF_CHEST = (1, 300)
        self.LEVEL = 1

        self.start_health_points = 10
        x0, y0 = (self.WIDTH) // 2, (self.HEIGHT) // 2

        self.p = Creatures(0, x0, y0, 10, None, 5, 20, None, None, None, 0, 1, None, 2, None, 0, 0, None, None, 4, 4,
                           None, 0, 3, 5, load_image(f"hero_{choice([1, 2, 3, 4])}.png"))
        id = choice([0, 1, 2, 3, 4])
        self.p.weapon = Weapon(self.WEAPONS_DATA[id][0], x0, y0, *self.WEAPONS_DATA[id][1:], self.p)
        self.p.type_attack = self.p.weapon.type_attack
        self.p.attack = self.p.weapon.attack
        self.p.bullet_id = self.p.weapon.bullet_id

        # ui
        self.cur = pygame.sprite.Group()
        self.hp_bar = pygame.sprite.Group()
        Cur(self.cur)
        for i in range(10):
            if i % 2 == 0:
                HpBar(i * 32, 50, 'left', self.hp_bar)
            else:
                HpBar(i * 32, 50, 'right', self.hp_bar)

    def generation(self):

        self.room_x, self.room_y = self.map_size // 2, self.map_size // 2

        # генерация карт
        self.room_count = [0, 16 - 1]
        self.map = [[Room(None, None, -1, self)] * self.map_size for _ in range(self.map_size)]

        cells = [(self.map_size // 2, self.map_size // 2)]

        def check(cell):
            count = 0
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (cell[0] + i, cell[1] + j) in cells:
                        count += 1
            return count

        while self.room_count[0] != self.room_count[1]:
            cell = choice(cells)
            change = (choice(('x', 'y')), choice((-1, 1)))
            if change[0] == 'x':
                new_cell = (cell[0], cell[1] + change[1])
            else:
                new_cell = (cell[0] + change[1], cell[1])
            if new_cell not in cells and 0 <= new_cell[0] < self.map_size and 0 <= new_cell[1] < self.map_size and \
                    check(new_cell) <= 3:
                self.room_count[0] += 1

                cells.append(new_cell)
        boss_room = cells[-1]

        # генерация комнат
        for cell in cells:
            if cell != boss_room:
                room = Room(cell[0], cell[1], 0, self)
            else:
                room = Room(cell[0], cell[1], 1, self)
            self.map[cell[1]][cell[0]] = room

            # генерация комнаты
            room.generation(cell == boss_room)

            self.LOADING.update()
            self.LOADING.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(self.FPS)

        self.body()

    def body(self):
        room = self.map[self.room_y][self.room_x]
        if not room.is_visited:
            self.STAT['room'] += 1
            room.is_visited = True
        self.open_doors = False
        room.add_doors()

        aim = 0
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEMOTION:
                    self.cur.update(event.pos[0], event.pos[1])
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.p.processes['attack'] == -1:
                        self.p.processes['attack'] = 0
                        self.p.weapon.processes['attack'] = 0
                        delta_y = (self.p.y + self.p.height//2 - event.pos[1])
                        delta_x = (self.p.x + self.p.width//2 - event.pos[0])
                        a = atan(delta_y/delta_x)*180/pi
                        a = 90 - abs(a)
                        if delta_x > 0 and delta_y < 0:
                            a = 90 - a
                            a += 90
                        elif delta_x < 0 and delta_y < 0:
                            a += 180
                        elif delta_x < 0 and delta_y > 0:
                            a = 90 - a
                            a += 270
                        if self.p.weapon.rotated_x:
                            a = 360 - a
                        self.p.weapon.center = a
                        aim = event.pos
                        if aim[0] < self.p.x and self.p.rotate_x:
                            self.p.rotate_x = False
                            self.p.weapon.rotated_x = False
                        elif aim[0] > self.p.x and not self.p.rotate_x:
                            self.p.rotate_x = True
                            self.p.weapon.rotated_x = True

            if self.running:
                # заполнение экрана игроком, пулями, врагами
                pygame.display.update()
                # декорации
                room.all_decorations_sprites.draw(self.screen)

                # хп бар
                try:
                    k = int(10 * self.p.health_points / self.start_health_points)
                    while len(self.hp_bar) > k:
                        self.hp_bar.remove(self.hp_bar.sprites()[-1])
                    self.hp_bar.draw(self.screen)
                except IndexError:
                    pass

                # мини карта
                f1 = pygame.font.Font(None, 30)
                for i in range(self.map_size):
                    for j in range(self.map_size):
                        if i == self.room_x and j == self.room_y:
                            text1 = f1.render(str(self.map[j][i]), True, pygame.Color('green'))
                            self.screen.blit(text1, (i * self.WIDTH // 70 + self.WIDTH * 0.88, j * self.HEIGHT // 60))
                        elif type(self.map[j][i]) is not str:
                           if self.map[j][i].is_visited:
                               text1 = f1.render(str(self.map[j][i]), True, (0, 128, 255))
                               self.screen.blit(text1,
                                                 (i * self.WIDTH // 70 + self.WIDTH * 0.88, j * self.HEIGHT // 60))
                           else:
                               text1 = f1.render(str(self.map[j][i]), True, pygame.Color('white'))
                               self.screen.blit(text1,
                                                 (i * self.WIDTH // 70 + self.WIDTH * 0.88, j * self.HEIGHT // 60))
                        else:
                            text1 = f1.render(str(self.map[j][i]), True, pygame.Color('white'))
                            self.screen.blit(text1, (i * self.WIDTH // 70 + self.WIDTH * 0.88, j * self.HEIGHT // 60))

                # переход в другие комнаты
                if len(room.enemies) == 1:
                    if not self.open_doors:
                        for key in list(room.doors.keys()):
                            if room.doors[key] is not None:
                                room.doors[key].is_passable = 1
                                if key == 'door1':
                                    d1 = Decoration(11, 864, 0, *self.DECORATIONS_DATA[10][1:])
                                    room.all_decorations_sprites.remove(room.doors[key])
                                    room.all_decorations_sprites.add(d1)
                                    del room.decorations[room.decorations.index(room.doors[key])]
                                    room.decorations.append(d1)
                                    room.doors['door1'] = d1
                            self.open_doors = True

                room.all_bullets_sprites.update(room)
                room.all_bullets_sprites.draw(self.screen)

                self.p.weapon.update()

                for e in room.enemies:
                    e.timer += choice([0, 1, 2])
                    e.timer2 += choice([0, 1, 2])
                    if e.id == 4 and e.timer >= 1000 and e.processes['attack'] == -1 and e.processes['death'] == -1:
                        e.type_attack = 2
                        e.radius1, e.radius2 = e.radius2, e.radius1
                        e.attack1_moment1, e.attack1_moment2, e.attack2_moment1, \
                        e.attack2_moment2 = e.attack2_moment1, e.attack2_moment2, e.attack1_moment1, e.attack1_moment2
                        e.processes_sprites[1] = e.frames[e.attack2_pos]
                        e.timer = 0
                    elif e.id == 5 and e.timer >= 200 and e.processes['attack'] == -1 and e.processes['death'] == -1:
                        mob = self.MONSTERS_DATA[4]
                        tp = Creatures(mob[0], randint(0, 19) * 96, randint(3, 10) * 96, *mob[1:],
                                       load_image(f"monster_{mob[0]}.png"))
                        room.all_monsters_sprites.add(tp)
                        room.enemies.append(tp)
                        e.timer = 0
                        e.processes['death'] = 0
                    elif e.id == 8 and e.timer >= 500 and e.processes['attack'] == -1 and e.processes['death'] == -1:
                        if e.speed == 0.5:
                            e.speed = 5
                            e.processes_sprites[0] = e.frames[1][:(3 + 1) * e.fast]
                        else:
                            e.speed = 0.5
                            e.processes_sprites[0] = e.frames[0]
                        e.timer = 0
                    elif e.id == 11 and e.timer >= 200 and e.processes['attack'] == -1 and e.processes['death'] == -1:
                        if e.health_points < e.start_health_points:
                            e.health_points += 1
                        e.timer = 0
                    elif e.id == 12 and e.timer >= 800 and e.processes['attack'] == -1 and e.processes['death'] == -1:
                        e.processes['attack'] = 0
                        e.timer = 0
                    elif e.id == 15 and e.speed == 0.5 and e.timer >= 1200 and e.key == 0 and \
                            e.processes['attack'] == -1 and e.processes['death'] == -1:
                            e.speed = 0
                            e.processes_sprites[0] = e.frames[0][:(10 + 1) * e.fast]
                            e.timer = 0
                    elif e.id == 15 and e.speed == 0 and e.timer >= 400 and e.processes['attack'] == -1 and \
                            e.processes['death'] == -1:
                        e.speed = 0.5
                        e.processes_sprites[0] = e.frames[1]
                        e.timer = 0
                    elif e.id == 21 and e.timer >= 100 and e.processes['attack'] == -1 and\
                            e.processes['death'] == -1:
                        e.attack1_pos, e.attack2_pos = e.attack2_pos, e.attack1_pos
                        e.processes_sprites[1] = e.frames[e.attack2_pos]
                        e.timer = 0
                    elif e.id == 19 and e.timer >=300 and e.processes['attack'] == -1 and\
                            e.processes['death'] == -1:
                        e.type_attack = 2
                        e.radius1, e.radius2 = e.radius2, e.radius1
                        e.attack1_moment1, e.attack1_moment2, e.attack2_moment1, \
                        e.attack2_moment2 = e.attack2_moment1, e.attack2_moment2, e.attack1_moment1, e.attack1_moment2
                        e.processes_sprites[1] = e.frames[e.attack2_pos]
                    elif e.id == 22 and e.timer >= 150 and e.processes['attack'] == -1 and \
                            e.processes['death'] == -1 and e.type_attack == 1:
                        e.type_attack = 2
                        e.radius1, e.radius2 = e.radius2, e.radius1
                        e.attack1_moment1, e.attack1_moment2, e.attack2_moment1, \
                        e.attack2_moment2 = e.attack2_moment1, e.attack2_moment2, e.attack1_moment1, e.attack1_moment2
                        e.processes_sprites[1] = e.frames[e.attack2_pos]
                        e.timer = 0

                    if e.id == 19 and e.timer2 >= 200 and e.processes['attack'] == -1 and\
                            e.processes['death'] == -1:
                        mob = self.MONSTERS_DATA[18]
                        minion = Creatures(mob[0], randint(0, 19) * 96, randint(3, 10) * 96, *mob[1:],
                                       load_image(f"monster_{mob[0]}.png"))
                        room.all_monsters_sprites.add(minion)
                        room.enemies.append(minion)
                        e.timer2 = 0
                    elif e.id == 21 and e.timer2 >= 300 and e.processes['attack'] == -1 and\
                            e.processes['death'] == -1 and e.speed != 3:
                        e.speed = 3
                        e.processes_sprites[0] = e.frames[5][:(8 + 1) * e.fast]
                        e.timer2 = 0
                    elif e.id == 21 and e.timer2 >= 90 and e.processes['attack'] == -1 and\
                            e.processes['death'] == -1 and e.speed == 3:
                        e.speed = 1
                        e.processes_sprites[0] = e.frames[e.run_pos][:(e.end_of_run + 1) * e.fast]
                        e.timer2 = 0

                    if e.id not in (0, 12) and e.processes['attack'] == -1 and \
                            ((self.p.y + self.p.height / 2 - e.y - e.height / 2) ** 2 +
                            (self.p.x + self.p.width / 2 - e.x - e.width / 2) ** 2) ** 0.5 < e.radius1 and \
                            ((e.type_attack == 1 and abs((e.y + e.height / 2) - (self.p.y + self.p.height / 2))
                            < self.p.height // 2) or e.type_attack == 2) and not (e.id == 15 and e.speed == 0):
                        if e.id == 7 and e.processes['death'] == -1:
                            e.processes['death'] = 0
                        elif e.attack1_moment1 != -1:
                            e.processes['attack'] = 0

                    if e.invulnerability != 0:
                        e.invulnerability -= 1
                    e.processes['walking'] += 1
                    for key, time in list(e.processes.items()):
                        if key == 'attack' and time != -1 and e.processes['death'] == -1:
                            if e.type_attack == 2 and time == len(e.processes_sprites[1]):
                                e.processes[key] = -1

                                if e.id == 4:
                                    e.type_attack = 1
                                    e.radius1, e.radius2 = e.radius2, e.radius1
                                    e.attack1_moment1, e.attack1_moment2, e.attack2_moment1, \
                                    e.attack2_moment2 = e.attack2_moment1, e.attack2_moment2, e.attack1_moment1, \
                                                        e.attack1_moment2
                                    e.processes_sprites[1] = e.frames[e.attack1_pos]
                                elif e.id == 22:
                                    e.type_attack = 1
                                    e.radius1, e.radius2 = e.radius2, e.radius1
                                    e.attack1_moment1, e.attack1_moment2, e.attack2_moment1, \
                                    e.attack2_moment2 = e.attack2_moment1, e.attack2_moment2, e.attack1_moment1, e.attack1_moment2
                                    e.processes_sprites[1] = e.frames[e.attack1_pos]
                                elif e.id == 19:
                                    e.type_attack = 1
                                    e.radius1, e.radius2 = e.radius2, e.radius1
                                    e.attack1_moment1, e.attack1_moment2, e.attack2_moment1, \
                                    e.attack2_moment2 = e.attack2_moment1, e.attack2_moment2, e.attack1_moment1, \
                                                        e.attack1_moment2
                                    e.processes_sprites[1] = e.frames[e.attack1_pos]
                                    e.timer = 0

                            elif e.id == 12 and e.type_attack == 2 and time == e.attack1_moment1 * e.fast:
                                bullet_data = list(self.BULLETS_DATA[e.bullet_id - 1])
                                id1, speed1 = bullet_data

                                b1 = Bullet(id1, e.x + e.rect.width / 2, e.y + e.rect.height / 2, speed1,
                                           -speed1, 0, e, rotate=0)
                                room.all_bullets_sprites.add(b1)
                                room.bullets.append(b1)
                                b2 = Bullet(id1, e.x + e.rect.width / 2, e.y + e.rect.height / 2, speed1,
                                           -speed1/(2**0.5), -speed1/(2**0.5), e, rotate=135)
                                room.all_bullets_sprites.add(b2)
                                room.bullets.append(b2)
                                b3 = Bullet(id1, e.x + e.rect.width / 2, e.y + e.rect.height / 2, speed1,
                                           0, -speed1, e,  rotate=90)
                                room.all_bullets_sprites.add(b3)
                                room.bullets.append(b3)
                                b4 = Bullet(id1, e.x + e.rect.width / 2, e.y + e.rect.height / 2, speed1,
                                           speed1/(2**0.5), -speed1/(2**0.5), e, rotate=45)
                                room.all_bullets_sprites.add(b4)
                                room.bullets.append(b4)
                                b5 = Bullet(id1, e.x + e.rect.width / 2, e.y + e.rect.height / 2, speed1,
                                           speed1, 0, e,  rotate=180)
                                room.all_bullets_sprites.add(b5)
                                room.bullets.append(b5)

                                e.processes[key] += 1
                                e.processes['walking'] = -1
                                e.update(2)

                            elif e.type_attack == 2 and time == e.attack1_moment1 * e.fast:
                                if e == self.p:
                                    target = aim
                                elif e.id == 22:
                                    target = (self.p.x + self.p.width / 2, self.p.y - self.p.height/2)
                                else:
                                    target = (self.p.x + self.p. width/2, self.p.y + self.p.height/2)

                                bullet_data = list(self.BULLETS_DATA[e.bullet_id - 1])
                                id1, speed1 = bullet_data

                                s_y = target[1] - e.y - e.height / 2
                                s_x = target[0] - e.x - e.width / 2
                                if s_x < 0:
                                    k = -1
                                else:
                                    k = 1
                                try:
                                    k1 = s_y / s_x
                                except ZeroDivisionError:
                                    k1 = s_y
                                speed_x = k * speed1 / sqrt(k1 ** 2 + 1)
                                speed_y = k1 * speed_x

                                if e.id == 22:
                                    rotate1 = 0
                                else:
                                    rotate1 = (360 - (atan(s_y / s_x) * 180 / pi))
                                b = Bullet(id1, e.x + e.rect.width / 2, e.y + e.rect.height / 2, speed1,
                                           speed_x, speed_y, e, rotate=rotate1)
                                if e.id == 22:
                                    b.x = target[0]
                                    b.y = target[1]

                                b.x -= b.width // 2
                                b.y -=b.height // 2
                                room.all_bullets_sprites.add(b)
                                room.bullets.append(b)

                                e.processes[key] += 1
                                e.processes['walking'] = -1
                                e.update(2)

                            elif time == len(e.processes_sprites[1]):
                                e.processes[key] = -1
                                if e.id == 15:
                                    e.key = 1
                                    e.speed = 2
                                    if e.rotate_x:
                                        if e.x - 50 > 20:
                                            e.target = (e.x + e.width / 2 - 50, e.y + e.height / 2)
                                        else:
                                            e.target = (e.width / 2 + 20, e.y + e.height / 2)
                                    else:
                                        if e.x + 50 < self.WIDTH - 20:
                                            e.target = (e.x + e.width / 2 + 50, e.y + e.height / 2)
                                        else:
                                            e.target = (self.WIDTH - e.width / 2 - 20, e.y + e.height / 2)
                                    e.save_pos = (e.x + e.width/2, e.y + e.height/2)

                            else:
                                e.processes[key] += 1
                                e.processes['walking'] = -1
                                e.update(1)

                        elif key == 'death' and time != -1:
                            if time == len(e.processes_sprites[2]):
                                e.processes[key] = -1
                                self.STAT['kill'] += 1
                                if e == self.p:
                                    self.STAT['time'] = datetime.datetime.now() - self.t
                                    g = GameOverWindow(self.WIDTH, self.HEIGHT, self.FPS, self.screen, self.STAT)
                                elif e.id < 5 and randint(1, 100) >= 95:
                                    room.all_monsters_sprites.remove(e)
                                    del room.enemies[room.enemies.index(e)]
                                    mob = self.MONSTERS_DATA[5]
                                    soul = Creatures(mob[0], e.x, e.y, e.start_health_points//2, *mob[2:],
                                                  load_image(f"monster_{mob[0]}.png"))
                                    room.all_monsters_sprites.add(soul)
                                    room.enemies.append(soul)
                                elif e.id == 19 or e.id == 21 or e.id == 22:
                                    room.all_monsters_sprites.remove(e)
                                    del room.enemies[room.enemies.index(e)]
                                    self.STAT['boss_kill'] += 1
                                    # переход на след этаж
                                    self.STAT['loops'] += 1
                                    r = Decoration(12, randint(6, 10) * 96, randint(5, 7) * 96,
                                                   *self.DECORATIONS_DATA[12 - 1][1:])
                                    room.all_decorations_sprites.add(r)
                                    room.decorations.append(r)
                                else:
                                    room.all_monsters_sprites.remove(e)
                                    del room.enemies[room.enemies.index(e)]
                            else:
                                e.processes[key] += 1
                                e.processes['walking'] = -1
                                e.update(2)

                    speed_x = 0
                    speed_y = 0
                    if e.processes['walking'] != -1 and e != self.p:
                        if e.key < 1:
                            if e.x < self.p.x:
                                e.target = (self.p.x + self.p.width / 2 - e.radius1 + 1, self.p.y + self.p.height / 2)
                            else:
                                e.target = (self.p.x + self.p.width / 2 + e.radius1 - 1, self.p.y + self.p.height / 2)
                        s_x = (e.target[0] - e.x - e.width/2)
                        s_y = (e.target[1] - e.y - e.height/2)
                        if not (int(abs(s_x)) < 1 and int(abs(s_y)) < 1):
                            k = 1
                            if s_x < 0:
                                k = -1
                            try:
                                k1 = s_y / s_x
                            except ZeroDivisionError:
                                k1 = s_y

                            speed_x = k * e.speed / sqrt(k1 ** 2 + 1)
                            speed_y = k1 * speed_x
                            if e.x < self.p.x:
                                e.rotate_x = True
                            else:
                                e.rotate_x = False
                        elif e.id == 15:
                            if e.key == 1:
                                e.key = 2
                                e.target = e.save_pos
                            elif e.key == 2:
                                e.key = 0
                                e.speed = 0.5
                        e.update(0, speed_x=speed_x, speed_y=speed_y)

                    elif e.processes['walking'] != -1 and e == self.p and e.processes['death'] == -1:
                        # передвижение игрока
                        keys = pygame.key.get_pressed()
                        if keys[pygame.K_w] and self.p.y > 0:
                            speed_y = -self.p.speed
                        if keys[pygame.K_s] and self.p.y < self.HEIGHT - self.p.height:
                            speed_y = self.p.speed
                        if keys[pygame.K_a] and self.p.x > -self.p.radius1:
                            speed_x = -self.p.speed
                            e.rotate_x = False
                            if e.weapon.rotated_x:
                                e.weapon.rotated_x = False
                        if keys[pygame.K_d] and self.p.x < self.WIDTH - self.p.width + self.p.radius1:
                            speed_x = self.p.speed
                            e.rotate_x = True
                            if not e.weapon.rotated_x:
                                e.weapon.rotated_x = True
                        if keys[pygame.K_m]:
                            self.fps = 300
                        if keys[pygame.K_b]:
                            self.fps = 5
                        if keys[pygame.K_n]:
                            self.fps = 120
                        e.update(0, speed_x=speed_x, speed_y=speed_y)

                    # получил ли урон соприеосновением с пулями/врагами
                    for spr in pygame.sprite.spritecollide(e, room.all_monsters_sprites, False):
                        if (spr != self.p and e == self.p and e.invulnerability == 0 and
                                pygame.sprite.collide_mask(e, spr) and
                                ((spr.attack1_moment1 * spr.fast <= spr.processes['attack'] <=
                                spr.attack1_moment2 * spr.fast) or spr.attack1_moment1 == -1)) or \
                                (spr.id == 15 and spr != self.p and e == self.p and e.invulnerability == 0 and
                                 pygame.sprite.collide_mask(e, spr) and spr.attack2_moment1 * spr.fast <=
                                 spr.processes['attack'] <= spr.attack2_moment2 * spr.fast) or\
                                (spr.id == 7 and spr != self.p and e == self.p and e.invulnerability == 0 and
                                pygame.sprite.collide_mask(e, spr) and spr.attack1_moment1 * spr.fast <=
                                spr.processes['death'] <= spr.attack1_moment2 * spr.fast) or\
                                (spr.id == 12 and spr != self.p and e == self.p and e.invulnerability == 0 and
                                pygame.sprite.collide_mask(e, spr)):
                            if spr.id == 17:
                                e.health_points -= spr.attack * (spr.start_health_points - spr.health_points)
                                spr.health_points += spr.attack * (spr.start_health_points - spr.health_points)
                            else:
                                e.health_points -= spr.attack
                            e.invulnerability = 50
                            break
                    for spr in pygame.sprite.spritecollide(e, room.all_bullets_sprites, False):
                        if (not ((spr.author != self.p and e != self.p) or (spr.author == self.p and e == self.p)) and
                                e.invulnerability == 0 and pygame.sprite.collide_mask(e, spr)) and \
                                e.processes['death'] == -1:
                            if spr.id == 11 and spr.cur_frame < 40:
                                continue
                            if e.id == 9:
                                e.health_points -= 1
                            elif e.id == 12 and 2 * e.fast <= e.processes['attack'] <= 17 * e.fast:
                                e.health_points -= 0
                            elif e.id == 15 and e.speed == 0 and 2 * e.fast <= e.processes['walking'] <= 14 * e.fast:
                                if e.health_points + spr.author.attack > e.start_health_points:
                                    e.health_points = e.start_health_points
                                else:
                                    e.health_points += spr.author.attack
                            else:
                                e.health_points -= spr.author.attack
                                if spr.author == self.p:
                                    self.STAT['dmg'] += spr.author.attack
                                if e.id == 17:
                                    e.speed = e.start_speed * (e.start_health_points - e.health_points)
                                    print(e.speed)
                            e.invulnerability = 50
                            if spr.id != 11:
                                room.all_bullets_sprites.remove(spr)
                                del room.bullets[room.bullets.index(spr)]
                            break

                    for spr in pygame.sprite.spritecollide(e, room.all_weapons_sprites, False):

                        if spr.speed * 3 < spr.processes['attack']< spr.speed * 5 and e.invulnerability == 0 and \
                                pygame.sprite.collide_mask(e, spr) and e != self.p and spr.type_attack == 1:
                            if e.id == 9:
                                e.health_points -= 1
                            elif e.id == 12 and 2 * e.fast <= e.processes['attack'] <= 17 * e.fast:
                                e.health_points -= 0
                            elif e.id == 15 and e.speed == 0 and 2 * e.fast <= e.processes['walking'] <= 14 * e.fast:
                                if e.health_points + spr.author.attack > e.start_health_points:
                                    e.health_points = e.start_health_points
                                else:
                                    e.health_points += spr.author.attack
                            else:
                                e.health_points -= spr.attack
                                self.STAT['dmg'] += spr.attack
                                if e.id == 17:
                                    e.speed = e.speed * (e.start_health_points - e.health_points)
                            e.invulnerability = 50
                            break

                    for spr in reversed(pygame.sprite.spritecollide(e, room.all_decorations_sprites, False)):
                        if not spr.is_penetrable and e.processes['attack'] == -1 and e == self.p:
                            if spr in list(room.doors.values()) and len(room.enemies) == 1:
                                index = list(room.doors.values()).index(spr)
                                if index == 0 and room.doors['door1'] is not None:
                                    self.room_y -= 1
                                    self.p.y = self.HEIGHT - 80 - self.p.height
                                elif index == 1 and room.doors['door2'] is not None:
                                    self.room_y += 1
                                    self.p.y = 192 + self.p.height
                                elif index == 2 and room.doors['door3'] is not None:
                                    self.room_x -= 1
                                    self.p.x = self.WIDTH - 40 - self.p.width
                                elif index == 3 and room.doors['door4'] is not None:
                                    self.room_x += 1
                                    self.p.x = 40

                                room.bullets = []
                                room.all_bullets_sprites = pygame.sprite.Group()
                                room = self.map[self.room_y][self.room_x]
                                if not room.is_visited:
                                    self.STAT['room'] += 1
                                    room.is_visited = True
                                self.open_doors = False
                                room.add_doors()
                            if spr.y < e.y and speed_y < 0:
                                e.update(0, speed_y=-speed_y)
                            if spr.x > e.x and speed_x > 0:
                                e.update(0, speed_x=-speed_x)
                            if spr.y > e.y and speed_y > 0:
                                e.update(0, speed_y=-speed_y)
                            if spr.x < e.x and speed_x < 0:
                                e.update(0, speed_x=-speed_x)
                        elif spr.id == 12 and e == self.p and pygame.sprite.collide_mask(e, spr) and \
                                pygame.key.get_pressed()[pygame.K_e]:
                            self.LEVEL += 1
                            # проверка конца игры
                            if self.LEVEL == 4:
                                self.STAT['win_game'] = True
                                self.STAT['time'] = datetime.datetime.now() - self.t
                                g = GameOverWindow(self.WIDTH, self.HEIGHT, self.FPS, self.screen, self.STAT)
                            self.LOADING = pygame.sprite.Group(Picture('game.png'), Loading(430, 910))
                            self.LOADING.draw(self.screen)
                            self.generation()

                    # смерть
                    if e.health_points <= 0 and e.processes['death'] == -1:
                        e.processes['death'] = 0

                room.all_monsters_sprites.draw(self.screen)
                room.all_weapons_sprites.draw(self.screen)
            # курсор
            if pygame.mouse.get_focused():
                self.cur.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(self.FPS)
        pygame.quit()


class MainWindow:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Dungeons and (I'll come up with later)")
        self.SIZE = self.WIDTH, self.HEIGHT = 1920, 1080
        self.screen = pygame.display.set_mode(self.SIZE)
        self.FPS = 120
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.running = True
        self.all_sprites = pygame.sprite.Group()
        self.main_picture = Picture('main.png')
        self.all_sprites.add(self.main_picture)
        self.begin()

    def begin(self):
        while self.running:
            self.all_sprites.draw(self.screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            if any(pygame.key.get_pressed()):
                game = GameWindow(self.WIDTH, self.HEIGHT, self.FPS, self.screen)
                self.running = False

            pygame.display.flip()
            self.clock.tick(self.FPS)


m = MainWindow()
