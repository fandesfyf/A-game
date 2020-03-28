# -*-coding: utf-8 -*-
# encoding=utf-8
import arcade
import multiprocessing
import pygame
# import numpy
import random
# import numpy.random.common
# import numpy.random.bounded_integers
# import numpy.random.entropy
import timeit
import os
import math
import sys

# import ffmpeg
multiprocessing.freeze_support()

pygame.init()
# 一些想法:1.通过控制渲染范围来加速

# 3.加入联机
# 4.加入更多方块
# 5.加入药剂系统
# 6.优化奖励掉落
# 7.优化爆炸范围伤害
# 子弹相撞
# 加入命中率

# 地图缩放比例
SPRITE_SCALING = 0.3
SPRITE_SIZE = 90 * SPRITE_SCALING  # 网格边长

BULLET_SPEED = 8 * SPRITE_SCALING * 4  # 玩家子弹速度
E_BULLET_SPEED = 10 * SPRITE_SCALING * 3  # 敌人子弹速度

MOVEMENT_SPEED = 4 * SPRITE_SCALING * 3.2  # 移动速度
ENEMY_DAMAGE = 500  # 敌人标准攻击力

# 网格坐标边长
GRID_WIDTH = GRID_HEIGHT = 100

# Parameters for cellular automata
CHANCE_TO_START_ALIVE = 0.4
DEATH_LIMIT = 3
BIRTH_LIMIT = 4
NUMBER_OF_STEPS = 4

# 窗口大小
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Not a game"

# 是否水平合并
MERGE_SPRITES = False
# 屏幕滚动极限
SCROLL = 150
# 加载声音
hit_sound1 = arcade.sound.load_sound("files/sound/爆炸2.wav")  # 方块爆炸声
explosion_sound = arcade.load_sound("files/sound/爆炸.wav")  # 玩家子弹爆炸
f_sound = arcade.load_sound("files/sound/勘探导弹.wav")
e_sound = arcade.load_sound("files/sound/被激光击中爆炸.wav")

white = (255, 255, 255)
black = (0, 0, 0)
gray = (128, 128, 128)
red = (200, 0, 0)
green = (0, 200, 0)
bright_red = (255, 0, 0)
bright_green = (0, 255, 0)
blue = (50, 100, 195)
yellow = (255, 247, 200)
clo = (255, 0, 0)
# 玩家子弹爆炸纹理d
player_texture_list = []
for i in range(16):
    # Files from http://www.explosiongenerator.com are numbered sequentially.
    # This code loads all of the explosion0000.png to explosion0270.png files
    # that are part of this explosion.
    texture_name = f"files/explosion/explosion{i:04d}.png"
    print(i)

    player_texture_list.append(arcade.load_texture(texture_name))

# 另一个爆炸纹理(应用于敌人)(蓝色）
e_b_texture_list = []
for i in range(8):
    e_texture_name = f"files/explosion/e_b{i:04d}.png"

    e_b_texture_list.append(arcade.load_texture(e_texture_name))
# 爆炸纹理用于炮塔(红色）
t_b_texture_list = []
for i in range(6):
    e_texture_name1 = f"files/explosion/t_b{i:04d}.png"
    t_b_texture_list.append(arcade.load_texture(e_texture_name1))

# 炮塔爆炸纹理
s_b_texture_list = []
for i in range(10):
    e_texture_name2 = f"files/explosion/s{i:04d}.png"
    s_b_texture_list.append(arcade.load_texture(e_texture_name2))

# 纹理用于导弹
m_b_texture_list = []
for i in range(12):
    e_texture_name3 = f"files/explosion/ex{i:04d}.png"

    m_b_texture_list.append(arcade.load_texture(e_texture_name3))
# 玩家导弹
p_b_texture_list = []
for i in range(16):
    e_texture_name4 = f"files/explosion/px{i:04d}.png"
    p_b_texture_list.append(arcade.load_texture(e_texture_name4))


#  创建网格坐标列表
def create_grid(width, height):
    """ Create a two-dimensional grid of specified size. """
    return [[0 for x in range(width)] for y in range(height)]


def initialize_grid(grid):
    """ Randomly set grid locations to on/off based on chance. """
    height = len(grid)
    width = len(grid[0])
    for row in range(height):
        for column in range(width):
            if random.random() <= CHANCE_TO_START_ALIVE:
                grid[row][column] = 1


# 细胞分裂算法
def count_alive_neighbors(grid, x, y):
    """ Count neighbors that are alive. """
    height = len(grid)
    width = len(grid[0])
    alive_count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            neighbor_x = x + i
            neighbor_y = y + j
            if i == 0 and j == 0:
                continue
            elif neighbor_x < 0 or neighbor_y < 0 or neighbor_y >= height or neighbor_x >= width:
                # Edges are considered alive. Makes map more likely to appear naturally closed.
                alive_count += 1
            elif grid[neighbor_y][neighbor_x] == 1:
                alive_count += 1
    return alive_count


# 算法实施
def do_simulation_step(old_grid):
    """ Run a step of the cellular automaton. """
    height = len(old_grid)
    width = len(old_grid[0])
    new_grid = create_grid(width, height)
    for x in range(width):
        for y in range(height):
            alive_neighbors = count_alive_neighbors(old_grid, x, y)
            if old_grid[y][x] == 1:
                if alive_neighbors < DEATH_LIMIT:
                    new_grid[y][x] = 0
                else:
                    new_grid[y][x] = 1
            else:
                if alive_neighbors > BIRTH_LIMIT:
                    new_grid[y][x] = 1
                else:
                    new_grid[y][x] = 0
    return new_grid


# 加成
class Stuff(arcade.Sprite):
    def __init__(self, file, sprite_scaling, armor, damage, hp, speed):
        super().__init__(file, sprite_scaling)
        self.Armor = armor
        self.Damage = damage
        self.HP = hp
        self.Speed = speed


# 方块
class Block(arcade.Sprite):
    def __init__(self, file, sprite_scaling, blood):
        super().__init__(file, sprite_scaling)
        self.blood = blood

    def update(self):
        if self.blood <= 0:
            self.kill()

    def kill(self):
        # arcade.sound.play_sound(hit_sound1)
        super().kill()


# 普通子弹
class Bullets(arcade.Sprite):
    def __init__(self, file, sprite_scaling, value, speed):
        super().__init__(file, sprite_scaling)
        self.value = value
        self.speed = speed


# 玩家子弹
class PlayerBullets(arcade.Sprite):
    def __init__(self, file, sprite_scaling, value, speed, e_b_list):
        super().__init__(file, sprite_scaling)
        # self.explosion_texture_list = player_texture_list
        self.value = value
        self.speed = speed
        self.e_b_list = e_b_list

    def explosion(self):
        explosion = Explosion(player_texture_list)
        explosion.center_x = self.center_x
        explosion.center_y = self.center_y
        arcade.sound.play_sound(explosion_sound)
        self.e_b_list.append(explosion)

    def kill(self):
        self.explosion()
        super().kill()


# 跟踪炮弹
class FollowBullets(arcade.Sprite):
    def __init__(self, file, sprite_scaling, value, speed, explosion_list):
        super().__init__(file, sprite_scaling)
        self.value = value
        self.speed = speed
        self.e_b_list = explosion_list

    def explosion(self):
        explosion = Explosion(m_b_texture_list)
        explosion.center_x = self.center_x
        explosion.center_y = self.center_y
        arcade.sound.play_sound(f_sound)
        self.e_b_list.append(explosion)

    def follow_sprite(self, player_sprite):
        """
        This function will move the current sprite towards whatever
        other sprite is specified as a parameter.

        We use the 'min' function here to get the sprite to line up withw
        the target sprite, and not jump around if the sprite is not off
        an exact multiple of SPRITE_SPEED.
        """

        self.center_x += self.change_x
        self.center_y += self.change_y

        # Random 1 in 100 chance that we'll change from our old direction and
        # then re-aim toward the player
        if random.randrange(10) == 0:
            start_x = self.center_x
            start_y = self.center_y

            # Get the destination location for the bullet
            dest_x = player_sprite.center_x
            dest_y = player_sprite.center_y

            # Do math to calculate how to get the bullet to the destination.
            # Calculation the angle in radians between the start points
            # and end points. This is the angle the bullet will travel.
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            angle = math.atan2(y_diff, x_diff)
            start_angle = self.angle
            self.angle = math.degrees(angle)
            dest_angle = self.angle
            angle_diff = dest_angle - start_angle
            # print(angle_diff)
            if angle_diff >= 30 or angle_diff <= -30:
                self.kill()

            # Taking into account the angle, calculate our change_x
            # and change_y. Velocity is how fast the bullet travels.
            self.change_x = math.cos(angle) * self.speed
            self.change_y = math.sin(angle) * self.speed

    def kill(self):
        self.explosion()
        super().kill()


# 玩家跟踪炮弹
class P_FollowBullets(arcade.Sprite):
    def __init__(self, file, sprite_scaling, value, speed, explosion_list, sprite):
        super().__init__(file, sprite_scaling)
        self.value = value
        self.speed = speed
        self.e_b_list = explosion_list
        self.sprite = sprite

    def explosion(self):
        explosion = Explosion(p_b_texture_list)
        explosion.center_x = self.center_x
        explosion.center_y = self.center_y
        arcade.sound.play_sound(f_sound)
        self.e_b_list.append(explosion)

    def follow_sprite(self):
        """
        This function will move the current sprite towards whatever
        other sprite is specified as a parameter.

        We use the 'min' function here to get the sprite to line up withw
        the target sprite, and not jump around if the sprite is not off
        an exact multiple of SPRITE_SPEED.
        """

        self.center_x += self.change_x
        self.center_y += self.change_y

        # Random 1 in 100 chance that we'll change from our old direction and
        # then re-aim toward the player
        if random.randrange(10) == 0:
            start_x = self.center_x
            start_y = self.center_y

            # Get the destination location for the bullet
            dest_x = self.sprite.center_x
            dest_y = self.sprite.center_y

            # Do math to calculate how to get the bullet to the destination.
            # Calculation the angle in radians between the start points
            # and end points. This is the angle the bullet will travel.
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            angle = math.atan2(y_diff, x_diff)
            start_angle = self.angle
            self.angle = math.degrees(angle)
            dest_angle = self.angle
            angle_diff = dest_angle - start_angle
            # print(angle_diff)
            if angle_diff >= 30 or angle_diff <= -30:
                self.kill()

            # Taking into account the angle, calculate our change_x
            # and change_y. Velocity is how fast the bullet travels.
            self.change_x = math.cos(angle) * self.speed
            self.change_y = math.sin(angle) * self.speed

    def update(self):
        self.follow_sprite()
        super().update()

    def kill(self):
        self.explosion()
        super().kill()


# boos类
class Boss(arcade.Sprite):
    def __init__(self, file, sprite_scaling, max_blood, armor, speed, e_b_list):
        super().__init__(file, sprite_scaling)
        self.blood = max_blood
        self.armor = armor
        self.speed = speed
        self.e_b_list = e_b_list

    def fire(self, player_sprite, t_bullet_list):

        if player_sprite.respawning == 0:

            if random.randint(0, 10) == 1:
                t_bullet1 = Bullets("files/激光2.png", SPRITE_SCALING, (ENEMY_DAMAGE * 2 / 5) * random.randint(1, 5),
                                    E_BULLET_SPEED * random.uniform(1, 1.5))

                b_start_x = self.center_x + 30 / math.sin(math.radians(self.angle))
                b_start_y = self.center_y + 30 / math.cos(math.radians(self.angle))
                t_bullet1.center_x = b_start_x
                t_bullet1.center_y = b_start_y

                start_x = self.center_x
                start_y = self.center_y
                # Get the destination location for the bullet
                # error = random.randint(-50, 50)
                dest_x = player_sprite.center_x
                dest_y = player_sprite.center_y

                # Do math to calculate how to get the bullet to the destination.
                # Calculation the angle in radians between the start points
                # and end points. This is the angle the bullet will travel.
                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                bx_diff = dest_x - b_start_x
                by_diff = dest_y - b_start_y
                angle = math.atan2(y_diff, x_diff)
                bangle = math.atan2(by_diff, bx_diff)
                self.angle = math.degrees(angle) - 90
                t_bullet1.angle = math.degrees(bangle)

                # print(f"Bullet angle: {self.bullet.angle:.2f}")
                # arcade.play_sound(self.gun_sound)

                # Taking into account the angle, calculate our change_x
                # and change_y. Velocity is how fast the bullet travels.
                t_bullet1.change_x = math.cos(bangle) * t_bullet1.speed
                t_bullet1.change_y = math.sin(bangle) * t_bullet1.speed

                # Add the bullet to the appropriate lists
                t_bullet_list.append(t_bullet1)

    def fire2(self, player_sprite, ft_bullet_list, explosion_list):

        if player_sprite.respawning == 0:

            if random.randrange(25) == 1:
                t_bullet2 = FollowBullets("files/子弹.png", SPRITE_SCALING,
                                          (ENEMY_DAMAGE * 2 / 5) * random.uniform(0.5, 3),
                                          E_BULLET_SPEED * random.uniform(1, 1.5), explosion_list)
                start_x = self.center_x
                start_y = self.center_y
                t_bullet2.center_x = start_x
                t_bullet2.center_y = start_y

                # Get the destination location for the bullet
                # error = random.randint(-50, 50)
                dest_x = player_sprite.center_x
                dest_y = player_sprite.center_y

                # Do math to calculate how to get the bullet to the destination.
                # Calculation the angle in radians between the start points
                # and end points. This is the angle the bullet will travel.
                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                angle = math.atan2(y_diff, x_diff)
                self.angle = math.degrees(angle) - 90
                t_bullet2.angle = math.degrees(angle)

                # print(f"Bullet angle: {self.bullet.angle:.2f}")
                # arcade.play_sound(self.gun_sound)

                # Taking into account the angle, calculate our change_x
                # and change_y. Velocity is how fast the bullet travels.
                t_bullet2.change_x = math.cos(angle) * t_bullet2.speed
                t_bullet2.change_y = math.sin(angle) * t_bullet2.speed

                # Add the bullet to the appropriate lists
                ft_bullet_list.append(t_bullet2)

    def follow_sprite(self, player_sprite):
        """
        This function will move the current sprite towards whatever
        other sprite is specified as a parameter.

        We use the 'min' function here to get the sprite to line up withw
        the target sprite, and not jump around if the sprite is not off
        an exact multiple of SPRITE_SPEED.
        """

        self.center_x += self.change_x
        self.center_y += self.change_y

        # Random 1 in 100 chance that we'll change from our old direction and
        # then re-aim toward the player
        if random.randrange(50) == 0:
            start_x = self.center_x
            start_y = self.center_y

            # Get the destination location for the bullet
            dest_x = player_sprite.center_x
            dest_y = player_sprite.center_y

            # Do math to calculate how to get the bullet to the destination.
            # Calculation the angle in radians between the start points
            # and end points. This is the angle the bullet will travel.
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            angle = math.atan2(y_diff, x_diff)
            self.angle = math.degrees(angle) - 90
            # print(angle)

            # Taking into account the angle, calculate our change_x
            # and change_y. Velocity is how fast the bullet travels.
            self.change_x = math.cos(angle) * self.speed
            self.change_y = math.sin(angle) * self.speed

    def follow_fire(self, player_sprite, ft_bullet_list, explosion_list):
        if player_sprite.respawning == 0:

            if random.randrange(200) == 1:
                t_bullet2 = FollowBullets("files/导弹2.png", SPRITE_SCALING, 2000 * random.uniform(0.5, 3),
                                          6 * random.uniform(1, 1.5), explosion_list)
                start_x = self.center_x
                start_y = self.center_y
                t_bullet2.center_x = start_x
                t_bullet2.center_y = start_y

                # Get the destination location for the bullet
                # error = random.randint(-50, 50)
                dest_x = player_sprite.center_x
                dest_y = player_sprite.center_y

                # Do math to calculate how to get the bullet to the destination.
                # Calculation the angle in radians between the start points
                # and end points. This is the angle the bullet will travel.
                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                angle = math.atan2(y_diff, x_diff)
                self.angle = math.degrees(angle) - 90
                t_bullet2.angle = math.degrees(angle)

                # print(f"Bullet angle: {self.bullet.angle:.2f}")
                # arcade.play_sound(self.gun_sound)

                # Taking into account the angle, calculate our change_x
                # and change_y. Velocity is how fast the bullet travels.
                t_bullet2.change_x = math.cos(angle) * t_bullet2.speed
                t_bullet2.change_y = math.sin(angle) * t_bullet2.speed

                # Add the bullet to the appropriate lists
                ft_bullet_list.append(t_bullet2)

    def update(self):
        super().update()
        if self.blood <= 0:
            self.kill()

    def explosion(self):
        explosion = Explosion(s_b_texture_list + m_b_texture_list)
        explosion.center_x = self.center_x
        explosion.center_y = self.center_y
        arcade.sound.play_sound(f_sound)
        self.e_b_list.append(explosion)

    def kill(self):
        self.explosion()
        super().kill()


# 炮塔类
class Tower(arcade.Sprite):
    def __init__(self, file, sprite_scaling, max_blood, armor, e_b_list):
        super().__init__(file, sprite_scaling)
        self.blood = max_blood
        self.armor = armor
        self.e_b_list = e_b_list
        # self.t_bullet1 = Bullets("files/激光1.png", SPRITE_SCALING_LASER, 50 * random.randint(1, 10),
        #                     10 * random.uniform(0.8, 1.8))
        # self.t_bullet2 = Bullets("files/火箭1.png", 1, 100 * random.randint(1, 5),
        #                           3 * random.uniform(0.8, 1.8))

    def explosion(self):
        explosion = Explosion(s_b_texture_list)
        explosion.center_x = self.center_x
        explosion.center_y = self.center_y
        arcade.sound.play_sound(f_sound)
        self.e_b_list.append(explosion)

    def fire(self, player_sprite, t_bullet_list):

        if player_sprite.respawning == 0:

            if random.randint(0, 10) == 1:
                t_bullet1 = Bullets("files/激光1.png", SPRITE_SCALING, ENEMY_DAMAGE * 0.2 * random.randint(1, 5),
                                    E_BULLET_SPEED)
                arcade.sound.play_sound(e_sound)
                start_x = self.center_x
                start_y = self.center_y
                t_bullet1.center_x = start_x
                t_bullet1.center_y = start_y

                # Get the destination location for the bullet
                # error = random.randint(-50, 50)
                dest_x = player_sprite.center_x
                dest_y = player_sprite.center_y

                # Do math to calculate how to get the bullet to the destination.
                # Calculation the angle in radians between the start points
                # and end points. This is the angle the bullet will travel.
                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                angle = math.atan2(y_diff, x_diff)
                self.angle = math.degrees(angle) - 90
                t_bullet1.angle = math.degrees(angle)

                # print(f"Bullet angle: {self.bullet.angle:.2f}")
                # arcade.play_sound(self.gun_sound)

                # Taking into account the angle, calculate our change_x
                # and change_y. Velocity is how fast the bullet travels.
                t_bullet1.change_x = math.cos(angle) * t_bullet1.speed
                t_bullet1.change_y = math.sin(angle) * t_bullet1.speed

                # Add the bullet to the appropriate lists
                t_bullet_list.append(t_bullet1)

    def kill(self):
        self.explosion()
        super().kill()

    def follow_fire(self, player_sprite, ft_bullet_list, explosion_list):
        if player_sprite.respawning == 0:

            if random.randrange(600) == 1:
                t_bullet2 = FollowBullets("files/导弹.png", SPRITE_SCALING, ENEMY_DAMAGE * 2 * random.randint(1, 4),
                                          E_BULLET_SPEED / 2, explosion_list)
                start_x = self.center_x
                start_y = self.center_y
                t_bullet2.center_x = start_x
                t_bullet2.center_y = start_y

                # Get the destination location for the bullet
                # error = random.randint(-50, 50)
                dest_x = player_sprite.center_x
                dest_y = player_sprite.center_y

                # Do math to calculate how to get the bullet to the destination.
                # Calculation the angle in radians between the start points
                # and end points. This is the angle the bullet will travel.
                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                angle = math.atan2(y_diff, x_diff)
                self.angle = math.degrees(angle) - 90
                t_bullet2.angle = math.degrees(angle)

                # print(f"Bullet angle: {self.bullet.angle:.2f}")
                # arcade.play_sound(self.gun_sound)

                # Taking into account the angle, calculate our change_x
                # and change_y. Velocity is how fast the bullet travels.
                t_bullet2.change_x = math.cos(angle) * t_bullet2.speed
                t_bullet2.change_y = math.sin(angle) * t_bullet2.speed

                # Add the bullet to the appropriate lists
                ft_bullet_list.append(t_bullet2)

    def update(self):
        super().update()
        if self.blood <= 0:
            self.kill()


# 敌人小兵类
class E_Sprite(arcade.Sprite):
    def __init__(self, file, sprite_scaling, max_blood):
        super().__init__(file, sprite_scaling)
        self.blood = max_blood
        self.bullet = Bullets("files/激光.png", SPRITE_SCALING, ENEMY_DAMAGE * 0.2 * random.uniform(1, 5), 20)

    def fire(self, player_sprite, bullet_list):
        if player_sprite.respawning == 0:

            if random.randint(0, 30) == 1:
                # Random 1 in 100 chance that we'll change from our old direction and
                # then re-aim toward the player
                arcade.sound.play_sound(e_sound)
                start_x = self.center_x
                start_y = self.center_y
                self.bullet.center_x = start_x
                self.bullet.center_y = start_y

                # Get the destination location for the bullet
                # error = random.randint(-50, 50)
                dest_x = player_sprite.center_x
                dest_y = player_sprite.center_y

                # Do math to calculate how to get the bullet to the destination.
                # Calculation the angle in radians between the start points
                # and end points. This is the angle the bullet will travel.
                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                angle = math.atan2(y_diff, x_diff)
                self.angle = math.degrees(angle) - 90
                self.bullet.angle = math.degrees(angle)

                # print(f"Bullet angle: {self.bullet.angle:.2f}")
                # arcade.play_sound(self.gun_sound)

                # Taking into account the angle, calculate our change_x
                # and change_y. Velocity is how fast the bullet travels.a
                self.bullet.change_x = math.cos(angle) * self.bullet.speed
                self.bullet.change_y = math.sin(angle) * self.bullet.speed

                # Add the bullet to the appropriate lists
                bullet_list.append(self.bullet)

    def follow_sprite(self, player_sprite):
        """
        This function will move the current sprite towards whatever
        other sprite is specified as a parameter.

        We use the 'min' function here to get the sprite to line up withw
        the target sprite, and not jump around if the sprite is not off
        an exact multiple of SPRITE_SPEED.
        """

        self.center_x += self.change_x
        self.center_y += self.change_y

        # Random 1 in 100 chance that we'll change from our old direction and
        # then re-aim toward the player
        if random.randrange(20) == 0:
            start_x = self.center_x
            start_y = self.center_y

            # Get the destination location for the bullet
            dest_x = player_sprite.center_x
            dest_y = player_sprite.center_y

            # Do math to calculate how to get the bullet to the destination.
            # Calculation the angle in radians between the start points
            # and end points. This is the angle the bullet will travel.
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            angle = math.atan2(y_diff, x_diff)
            self.angle = math.degrees(angle) - 90
            # print(angle)

            # Taking into account the angle, calculate our change_x
            # and change_y. Velocity is how fast the bullet travels.
            self.change_x = math.cos(angle) * MOVEMENT_SPEED / 8
            self.change_y = math.sin(angle) * MOVEMENT_SPEED / 8

    def update(self):
        if self.blood <= 0:
            self.kill()


# 玩家类
class HeroSprite(arcade.Sprite):
    def __init__(self, file, sprite_scaling, max_blood, armor, atk, move_speed):
        super().__init__(file, sprite_scaling)
        self.blood = max_blood
        self.max_blood = max_blood
        self.Armor = armor
        self.Damage = atk
        self.Speed = move_speed
        self.respawning = 0
        self.ATK = atk

        # Mark that we are respawning.
        self.respawn()

    def follow_fire(self, sprite, ft_bullet_list, explosion_list):

        t_bullet2 = P_FollowBullets("files/Double Dragon Neon-0.png", SPRITE_SCALING, 100 * random.uniform(0.5, 2),
                                    BULLET_SPEED / 2, explosion_list, sprite)
        start_x = self.center_x
        start_y = self.center_y
        t_bullet2.center_x = start_x
        t_bullet2.center_y = start_y

        dest_x = sprite.center_x
        dest_y = sprite.center_y

        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)
        self.angle = math.degrees(angle) - 90
        t_bullet2.angle = math.degrees(angle)

        # print(f"Bullet angle: {self.bullet.angle:.2f}")
        # arcade.play_sound(self.gun_sound)

        # Taking into account the angle, calculate our change_x
        # and change_y. Velocity is how fast the bullet travels.
        t_bullet2.change_x = math.cos(angle) * t_bullet2.speed
        t_bullet2.change_y = math.sin(angle) * t_bullet2.speed

        # Add the bullet to the appropriate lists
        ft_bullet_list.append(t_bullet2)

    def respawn(self):
        """
        Called when we die and need to make a new ship.
        'respawning' is an invulnerability timer.
        """
        # If we are in the middle of respawning, this is non-zero.
        self.respawning = 1
        # max_x = GRID_WIDTH * SPRITE_SIZE
        # max_y = GRID_HEIGHT * SPRITE_SIZE
        # self.center_x = random.randrange(max_x)
        # self.center_y = random.randrange(max_y)
        self.blood = self.max_blood

        self.angle = 0

    def update(self):
        # super().update()

        # pass

        # if self.blood <= 0:
        #     self.respawn()

        if self.respawning:
            self.respawning += 1
            self.alpha = self.respawning
            if self.respawning > 250:
                self.respawning = 0
                self.alpha = 255
        # super().update()


# 爆炸类
class Explosion(arcade.Sprite):
    """ This class creates an explosion animation """

    # Static variable that holds all the explosion textures
    explosion_textures = []

    def __init__(self, texture_list):
        super().__init__("files/explosion/explosion.png")

        # Start at the first frame
        self.current_texture = 0
        self.textures = texture_list

    def update(self):

        # Update to the next frame of the animation. If we are at the end
        # of our frames, then delete this sprite.
        self.current_texture += 1
        if self.current_texture < len(self.textures):
            self.set_texture(self.current_texture)
        else:
            self.kill()


# 游戏主体类
class Mygame(arcade.Window):
    # 为提高游戏打开速度，初始化中不放入过多代码
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, fullscreen=False, resizable=True)

        # 设定工作目录，使其打包后能工作
        # as mentioned at the top of this program.
        # file_path = os.path.dirname(os.path.abspath(__file__))
        try:
            file_path = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # import sys
            file_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        os.chdir(file_path)
        # 初始化分数
        self.score = 0
        # 计数boss死亡
        self.n = 1
        # self.fscore = 500
        self.DEF = 0
        self.firecount = 1
        self.textline = 1

        self.grid = None
        self.wall_list = None
        self.player_list = None
        self.boss_list = None
        self.enemy_list = None
        self.tower_list = None
        self.f_tower_list = None
        self.bullet_list = None
        self.bullet_list1 = None
        self.f_bullet_list = None
        self.e_bullet_list = None
        self.explosions_list = None
        self.e_b_list = None  # 爆炸列表！！
        self.t_bullet_list = None
        self.stuff_list = None

        self.player_sprite = None
        self.boss_sprite = None

        self.background = None

        self.view_bottom = 0
        self.view_left = 0
        self.draw_time = 0
        self.physics_engine = None  # 物理引擎

        # 鼠标事件
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.x = None
        self.y = None

        self.start = False
        self.fire = False
        self.show = False

        self.zx1 = arcade.Sprite("files/准星.png", SPRITE_SCALING)

        pygame.mixer.init()
        # pygame.mixer.music.load("./files/sound/bgm2.mp3")
        # pygame.mixer.music.play(-1)
        # self.hit_sound = arcade.sound.load_sound("files/sound/爆炸.mp3")
        # self.hit_sound1 = arcade.sound.load_sound("files/sound/爆炸2.mp3")
        # self.e_hit_sound = arcade.sound.load_sound("files/sound/爆炸3.mp3")

        # 加载声音文件
        self.gun_sound = arcade.sound.load_sound("files/sound/步枪火箭.wav")

        arcade.set_background_color(arcade.color.BANANA_MANIA)

    # 用于构造开始界面
    def startgame(self):
        self.start = False

        pygame.mixer.music.load("./files/sound/bgm1.mp3")
        pygame.mixer.music.play(-1)
        self.background = arcade.load_texture("files/background{}.png".format(random.randint(1, 6)))
        # arcade.set_background_color(arcade.color.AERO_BLUE)
        arcade.draw_texture_rectangle(self.width // 2, self.height // 2,
                                      self.width, self.height, self.background)

    def setup(self):  # 在setup中初始化游戏资源
        print("set up")
        arcade.set_background_color(arcade.color.AERO_BLUE)

        pygame.mixer.music.load("./files/sound/bgm2.mp3")
        pygame.mixer.music.play(-1)
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.player_list = arcade.SpriteList()
        self.boss_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.tower_list = arcade.SpriteList()
        self.f_tower_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.bullet_list1 = arcade.SpriteList()

        self.f_bullet_list = arcade.SpriteList()
        self.e_bullet_list = arcade.SpriteList()
        self.explosions_list = arcade.SpriteList()
        self.e_b_list = arcade.SpriteList()
        self.t_bullet_list = arcade.SpriteList()
        self.stuff_list = arcade.SpriteList()
        self.zx_list = arcade.SpriteList()

        self.zx2 = arcade.Sprite("files/准星2.png", SPRITE_SCALING)
        # arcade.play_sound(arcade.load_sound("files/sound/bgm2.mp3"))
        # output = "正在生成随机地图"
        # arcade.draw_text(output,
        #                  self.view_left + 20,
        #                  60 + self.view_bottom,
        #                  arcade.color.RED, 16)
        # 根据细胞分裂机创建随机地图各坐标数值
        self.grid = create_grid(GRID_WIDTH, GRID_HEIGHT)
        initialize_grid(self.grid)
        for step in range(NUMBER_OF_STEPS):
            self.grid = do_simulation_step(self.grid)
        # 改变边缘坐标数值
        for column in range(GRID_WIDTH):
            self.grid[0][column] = 1
            self.grid[GRID_HEIGHT - 1][column] = 1
        for row in range(GRID_HEIGHT):
            self.grid[row][0] = 1
            self.grid[row][GRID_WIDTH - 1] = 1

        # 根据数值设置各坐标方块
        if not MERGE_SPRITES:
            # 不水平合并
            for row in range(GRID_HEIGHT):
                # row column 为坐标
                for column in range(GRID_WIDTH):

                    if self.grid[row][column] == 1:
                        wall = Block("files/box.png", SPRITE_SCALING, 1000)

                        wall.center_x = column * SPRITE_SIZE + SPRITE_SIZE / 2
                        wall.center_y = row * SPRITE_SIZE + SPRITE_SIZE / 2
                        self.wall_list.append(wall)
                    if row == 0 or row == GRID_HEIGHT - 1 or column == 0 or column == GRID_WIDTH - 1:
                        wall2 = Block("files/boxx.png", SPRITE_SCALING, 5000)
                        wall2.center_x = column * SPRITE_SIZE + SPRITE_SIZE / 2
                        wall2.center_y = row * SPRITE_SIZE + SPRITE_SIZE / 2
                        self.wall_list.append(wall2)

        else:
            # 水平合并(更改MERGE_SPRITES,否则不执行!)
            # This uses new Arcade 1.3.1 features, that allow me to create a
            # larger sprite with a repeating texture. So if there are multiple
            # cells in a row with a wall, we merge them into one sprite, with a
            # repeating texture for each cell. This reduces our sprite count.
            for row in range(GRID_HEIGHT):
                column = 0
                while column < GRID_WIDTH:
                    while column < GRID_WIDTH and self.grid[row][column] == 0:
                        column += 1
                    start_column = column
                    while column < GRID_WIDTH and self.grid[row][column] == 1:
                        column += 1
                    end_column = column - 1

                    column_count = end_column - start_column + 1
                    column_mid = (start_column + end_column) / 2

                    wall = Block("files/box.png", SPRITE_SCALING, 1000)
                    wall.center_x = column_mid * SPRITE_SIZE + SPRITE_SIZE / 2
                    wall.center_y = row * SPRITE_SIZE + SPRITE_SIZE / 2
                    wall.width = SPRITE_SIZE * column_count
                    self.wall_list.append(wall)

        # 放置玩家精灵
        self.player_sprite = HeroSprite("files/character0.png", SPRITE_SCALING, 50000, 50, 50, MOVEMENT_SPEED)
        placed = False
        while not placed:
            max_x = GRID_WIDTH * SPRITE_SIZE
            max_y = GRID_HEIGHT * SPRITE_SIZE
            self.player_sprite.center_x = random.randrange(max_x)
            self.player_sprite.center_y = random.randrange(max_y)

            # 判断是否与墙冲突
            walls_hit = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)
            if len(walls_hit) == 0:
                placed = True
        self.player_list.append(self.player_sprite)

        # 放置boss
        self.boss_sprite = Boss("files/boss.png", SPRITE_SCALING, 50000, 200, MOVEMENT_SPEED / 15, self.e_b_list)
        placed = False
        while not placed:

            # Randomly position
            max_x = GRID_WIDTH * SPRITE_SIZE
            max_y = GRID_HEIGHT * SPRITE_SIZE
            self.boss_sprite.center_x = random.randrange(max_x)
            self.boss_sprite.center_y = random.randrange(max_y)
            distance = arcade.get_distance_between_sprites(self.boss_sprite, self.player_sprite)
            if distance >= 800:
                placed = True
        self.boss_list.append(self.boss_sprite)

        # 放置敌人
        for i in range(int(GRID_HEIGHT * 1.5)):  # 根据地图计算敌人数目
            enemy = E_Sprite("files/敌人.png", SPRITE_SCALING, 100 * random.uniform(0.8, 8))
            enemy_placed_successfully = False
            # Keep trying until success
            while not enemy_placed_successfully:
                enemy.center_x = random.randrange(GRID_WIDTH * SPRITE_SIZE)
                enemy.center_y = random.randrange(GRID_HEIGHT * SPRITE_SIZE)
                #  hitting a wall？
                wall_hit_list = arcade.check_for_collision_with_list(enemy, self.wall_list)

                #  hitting another coin？
                enemy_hit_list = arcade.check_for_collision_with_list(enemy, self.enemy_list)

                if len(wall_hit_list) == 0 and len(enemy_hit_list) == 0:
                    enemy_placed_successfully = True
            self.enemy_list.append(enemy)

        # 放置加成
        for o in range(int(GRID_HEIGHT)):
            choice = random.randint(0, 3)
            if choice == 0:
                stuff = Stuff("files/stuff/防御加成.png", SPRITE_SCALING, 10, 0, 0, 0)
            elif choice == 1:
                stuff = Stuff("files/stuff/力量加成.png", SPRITE_SCALING, 0, 5, 0, 0)
            elif choice == 2:
                stuff = Stuff("files/stuff/回血.png", SPRITE_SCALING, 0, 0, 500, 0)
            elif choice == 3:
                stuff = Stuff("files/stuff/速度.png", SPRITE_SCALING, 0, 0, 0, 0.1)

            stuff_placed_successfully = False
            while not stuff_placed_successfully:
                # Position
                stuff.center_x = random.randrange(GRID_WIDTH * SPRITE_SIZE)
                stuff.center_y = random.randrange(GRID_HEIGHT * SPRITE_SIZE)
                # print(stuff.center_y)
                wall_hit_list = arcade.check_for_collision_with_list(stuff, self.wall_list)
                if len(wall_hit_list) == 0:
                    stuff_placed_successfully = True
            self.stuff_list.append(stuff)

        # 放置普通炮塔
        for u in range(int(GRID_HEIGHT / 5)):
            tower1 = Tower("files/炮塔.png", SPRITE_SCALING, 10000, 500, self.e_b_list)
            tower1_placed_successfully = False
            while not tower1_placed_successfully:
                tower1.center_x = random.randrange(GRID_WIDTH * SPRITE_SIZE)
                tower1.center_y = random.randrange(GRID_HEIGHT * SPRITE_SIZE)
                wall_hit_list = arcade.check_for_collision_with_list(tower1, self.wall_list)
                if len(wall_hit_list) == 0:
                    tower1_placed_successfully = True
            self.tower_list.append(tower1)

        # 放置跟踪导弹炮塔
        for u in range(int(GRID_HEIGHT / 10)):
            tower2 = Tower("files/炮塔2.png", SPRITE_SCALING, 10000, 500, self.e_b_list)
            tower2_placed_successfully = False
            while not tower2_placed_successfully:
                tower2.center_x = random.randrange(GRID_WIDTH * SPRITE_SIZE)
                tower2.center_y = random.randrange(GRID_HEIGHT * SPRITE_SIZE)
                wall_hit_list = arcade.check_for_collision_with_list(tower2, self.wall_list)
                if len(wall_hit_list) == 0:
                    tower2_placed_successfully = True
            self.f_tower_list.append(tower2)
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)

    def on_draw(self):

        """ Render the screen. """

        # 开始计算绘制时间
        draw_start_time = timeit.default_timer()

        arcade.start_render()

        if self.start:

            # Draw the sprites
            self.wall_list.draw()
            self.bullet_list.draw()
            self.bullet_list1.draw()
            self.e_bullet_list.draw()
            self.player_list.draw()
            self.boss_list.draw()
            self.enemy_list.draw()
            self.tower_list.draw()
            self.f_tower_list.draw()
            self.t_bullet_list.draw()
            self.f_bullet_list.draw()
            self.stuff_list.draw()

            self.explosions_list.draw()
            self.e_b_list.draw()

            # self.zx1.draw()
            # self.boss_sprite.draw()

            # Draw info on the screen
            block_count = len(self.wall_list)

            output = f"Block Count: {block_count}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             self.height - 20 + self.view_bottom,
                             red, 16)

            output = f"Drawing time: {self.draw_time:.3f}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             self.height - 40 + self.view_bottom,
                             red, 16)

            output = f"Processing time: {self.processing_time:.3f}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             self.height - 60 + self.view_bottom,
                             red, 16)
            output = f"SCORE: {self.score:.0f}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             150 + self.view_bottom,
                             arcade.color.RED, 18)
            output = f"HP: {self.player_sprite.blood:.0f}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             100 + self.view_bottom,
                             arcade.color.RED, 16)

            output = f"BOSS_HP: {self.boss_sprite.blood:.0f}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             120 + self.view_bottom,
                             arcade.color.RED, 16)

            output = f"DEF: {self.DEF:.0f}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             80 + self.view_bottom,
                             arcade.color.RED, 16)

            output = f"ATK: {self.player_sprite.ATK:.0f}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             60 + self.view_bottom,
                             arcade.color.RED, 16)

            output = f"SPD: {self.player_sprite.Speed:.1f}"
            arcade.draw_text(output,
                             self.view_left + 20,
                             40 + self.view_bottom,
                             arcade.color.RED, 16)
            # arcade.draw_lrtb_rectangle_outline(self.view_left,self.view_left+170,self.view_bottom+180,self.view_bottom,bright_red)
            # arcade.draw_lrtb_rectangle_outline(self.view_left, self.view_left + 250, self.view_bottom + self.height,
            #                                    self.view_bottom+ self.height-80, bright_red)
        else:
            arcade.draw_texture_rectangle(self.width // 2, self.height // 2,
                                          self.width, self.height, self.background)
            centerx = self.width / 2
            centery = self.height / 5
            if self.show:
                with open("files/info.txt", "r")as info:
                    text = info.readlines()

                    for i in range(1, 30):
                        try:
                            if len(text[i + self.textline]) > 1:
                                arcade.draw_text(text[i + self.textline], 0, 18 * (30 - i),
                                                 black, font_size=15)

                        except:
                            pass
                arcade.draw_text("Slide to scan \nClick to exit", self.width - 100, self.height - 100,
                                 red, font_size=30, anchor_x="center")
                # arcade.draw_text("Edit by fandes\n 2861114322@qq.com", self.width - 100, self.height - 150,
                #                  red, font_size=15, anchor_x="center")
                t = "All material resources come from the Internet and are for learning purposes only.\n" \
                    "If there is infringement, Contact to delete. \nEdit by fandes  2861114322@qq.com"
                arcade.draw_text(t, 380, self.height - 100,
                                 red, font_size=18, anchor_x="center")
            else:

                # pass
                # centerx = self.width / 2
                # centery = self.height / 5
                arcade.draw_text("Not a game", centerx, WINDOW_HEIGHT * 8 / 11,
                                 arcade.color.BLACK, font_size=100, anchor_x="center")
                arcade.draw_text("---v 0.1.5.190921", centerx + 100, WINDOW_HEIGHT * 7 / 11,
                                 arcade.color.BLACK, font_size=30, anchor_x="center")
                arcade.draw_lrtb_rectangle_filled(centerx - 80, centerx + 80,
                                                  centery + 250, centery + 200, blue)
                arcade.draw_text("Start", centerx, centery + 210,
                                 black, font_size=30, anchor_x="center")

                arcade.draw_lrtb_rectangle_filled(centerx - 80, centerx + 80,
                                                  centery + 180, centery + 130, green)
                arcade.draw_text("MAP SIZE", centerx, centery + 140,
                                 black, font_size=30, anchor_x="center")
                output_total = "{}*{}".format(str(GRID_HEIGHT), str(GRID_HEIGHT))
                arcade.draw_text(output_total, centerx + 100, centery + 140, arcade.color.RADICAL_RED, 30)

                arcade.draw_lrtb_rectangle_filled(centerx - 80, centerx + 80,
                                                  centery + 110, centery + 60, green)
                arcade.draw_text("SCALING", centerx, centery + 70,
                                 black, font_size=30, anchor_x="center")
                output_total = "{}".format(str(SPRITE_SCALING))
                arcade.draw_text(output_total, centerx + 100, centery + 70, arcade.color.RADICAL_RED, 30)

                arcade.draw_lrtb_rectangle_filled(centerx - 80, centerx + 80,
                                                  centery + 40, centery - 10, red)
                arcade.draw_text("Quit", centerx, centery,
                                 bright_green, font_size=30, font_name="Arial", anchor_x="center")
                with open("files/best_score.txt", "r")as best_score:
                    score = int(best_score.read())

                    arcade.draw_text("Best score:{}".format(str(score)), centerx + 100, centery + 210,
                                     bright_red, font_size=30)

                arcade.draw_lrtb_rectangle_filled(centerx - 260, centerx - 100,
                                                  centery + 110, centery + 60, green)
                arcade.draw_text("Fullscreen:{}".format(str(self.fullscreen)), centerx - 180, centery + 75,
                                 red, font_size=20, anchor_x="center")

                arcade.draw_ellipse_filled(self.width - 100, self.height - 50,
                                           60, 20, red)
                arcade.draw_text("some info-", self.width - 100, self.height - 60,
                                 black, font_size=20, font_name="Arial", anchor_x="center")
            # print(11)
        self.zx1.draw()

        self.draw_time = timeit.default_timer() - draw_start_time
        # super().on_draw()

    # def Button(self, text, left, right, top, bottom,  action=None):
    #     arcade.draw_lrtb_rectangle_filled(left, right,
    #                                       top, bottom, green)
    #     arcade.draw_text(text, WINDOW_WIDTH / 2, WINDOW_HEIGHT * 6 / 9,
    #                              arcade.color.BLACK, font_size=100, anchor_x="center")
    def on_mouse_motion(self, x, y, dx, dy):
        # if self.start:
        self.x = x
        self.y = y
        view_pos = self.get_viewport()
        dest_x = x + view_pos[0]
        dest_y = y + view_pos[2]
        self.zx1.center_x = dest_x
        self.zx1.center_y = dest_y
        if self.start:

            if random.randrange(2) == 1:
                start_x = self.player_sprite.center_x
                start_y = self.player_sprite.center_y

                view_pos = self.get_viewport()

                dest_x = x + view_pos[0]
                dest_y = y + view_pos[2]

                x_diff = dest_x - start_x
                y_diff = dest_y - start_y

                angle = math.atan2(y_diff, x_diff)  # 计算角度 弧度

                self.player_sprite.angle = math.degrees(angle) - 90
        # else:
        #     centerx = WINDOW_WIDTH / 2
        #     centery = 120
        #     if centerx - 50<x<centerx + 50 and centery + 200<y<centery + 240:
        #         # arcade.draw_text("Not a game", centerx, WINDOW_HEIGHT * 6 / 9,
        #         #                  arcade.color.BLACK, font_size=100, anchor_x="center")
        #         arcade.draw_lrtb_rectangle_filled(centerx - 50, centerx + 50,
        #                                           centery + 240, centery + 200, bright_green)
        #         arcade.draw_text("Start", centerx, centery + 200,
        #                          red, font_size=30, anchor_x="center")
        #     elif centerx - 50<x<centerx + 50 and centery + 130<y<centery + 170:
        #         arcade.draw_lrtb_rectangle_filled(centerx - 50, centerx + 50,
        #                                           centery + 170, centery + 130, bright_green)
        #         arcade.draw_text("Size", centerx, centery + 130,
        #                          red, font_size=30, anchor_x="center")
        #     elif centerx - 50<x<centerx + 50 and centery + 60<y<centery + 100:
        #         arcade.draw_lrtb_rectangle_filled(centerx - 50, centerx + 50,
        #                                           centery + 100, centery + 60, bright_green)
        #         arcade.draw_text("fa", centerx, centery + 60,
        #                          red, font_size=30, anchor_x="center")
        #     elif centerx - 50 < x < centerx + 50 and centery -10 < y < centery + 30:
        #         arcade.draw_lrtb_rectangle_filled(centerx - 50, centerx + 50,
        #                                           centery + 30, centery - 10, bright_green)
        #         arcade.draw_text("Quit", centerx, centery - 10,
        #                          red, font_size=30, anchor_x="center")

    def on_mouse_press(self, x, y, button, modifiers):
        global GRID_HEIGHT, SPRITE_SCALING, SPRITE_SIZE, BULLET_SPEED, E_BULLET_SPEED, MOVEMENT_SPEED
        if self.start:
            """
            Called whenever the mouse moves.
            """
            if button == arcade.MOUSE_BUTTON_LEFT:  # 鼠标左键点击
                self.fire = True
                self.x = x
                self.y = y
                # 创建玩家子弹
                bullet = PlayerBullets("files/火箭.png", SPRITE_SCALING, 50 * self.n, BULLET_SPEED,
                                       self.e_b_list)

                # Position

                start_x = self.player_sprite.center_x
                start_y = self.player_sprite.center_y
                bullet.center_x = start_x
                bullet.center_y = start_y

                view_pos = self.get_viewport()
                # print(view_pos)
                # print(self.player_sprite.center_x,self.player_sprite.center_y)
                # print (x,y)

                dest_x = x + view_pos[0]
                dest_y = y + view_pos[2]
                # print(x,y)

                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                # print(x_diff)
                angle = math.atan2(y_diff, x_diff)  # 计算角度 弧度

                self.player_sprite.angle = math.degrees(angle) - 90
                bullet.angle = math.degrees(angle)

                # print(f"Bullet angle: {bullet.angle:.2f}")
                arcade.play_sound(self.gun_sound)

                bullet.change_x = math.cos(angle) * bullet.speed
                bullet.change_y = math.sin(angle) * bullet.speed

                self.bullet_list.append(bullet)
                # self.physics_engine.update()


            elif button == arcade.MOUSE_BUTTON_RIGHT:  # 鼠标右键点击
                e_list = []
                e_list.extend(self.boss_list)
                e_list.extend(self.enemy_list)
                e_list.extend(self.tower_list)
                e_list.extend(self.f_tower_list)
                # print(e_list)
                a = arcade.get_closest_sprite(self.player_sprite, e_list)
                self.player_sprite.follow_fire(a[0], self.bullet_list1, self.e_b_list)
                # print(11)
        else:

            if self.show:
                if button == arcade.MOUSE_BUTTON_LEFT:
                    self.show = False

            else:
                centerx = self.width / 2
                centery = self.height / 5
                if centerx - 80 < x < centerx + 80 and centery + 200 < y < centery + 250:
                    self.setup()
                    self.set_fullscreen(self.fullscreen)
                    self.start = True
                elif centerx - 80 < x < centerx + 80 and centery + 130 < y < centery + 180:
                    if GRID_HEIGHT <= 800:
                        GRID_HEIGHT += 50

                    if GRID_HEIGHT > 800:
                        GRID_HEIGHT = 50

                elif centerx - 80 < x < centerx + 80 and centery + 60 < y < centery + 110:

                    if SPRITE_SCALING <= 1:
                        SPRITE_SCALING += 0.1
                    if SPRITE_SCALING > 1:
                        SPRITE_SCALING = 0.1
                    SPRITE_SCALING = float("{:.2f}".format(SPRITE_SCALING))
                elif centerx - 80 < x < centerx + 80 and centery - 10 < y < centery + 40:
                    arcade.close_window()
                    sys.exit()
                elif centerx - 260 < x < centerx - 100 and centery + 60 < y < centery + 110:

                    self.set_fullscreen(not self.fullscreen)
                    self.set_viewport(0, self.width, 0, self.height)
                elif self.width - 130 < x < self.width - 70 and self.height - 60 < y < self.height - 40:
                    self.show = True
                BULLET_SPEED = 8 * SPRITE_SCALING * 4
                E_BULLET_SPEED = 10 * SPRITE_SCALING * 3

                MOVEMENT_SPEED = 4 * SPRITE_SCALING * 3.2
                SPRITE_SIZE = 90 * SPRITE_SCALING

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.show:
            print(x, y, scroll_x, scroll_y)
            if scroll_y > 0:
                self.textline += 1
            if scroll_y < 0:
                self.textline -= 1
        #     pos = self.get_viewport()
        #     cx = self.width/10
        #     cy = self.height/10
        #     if scroll_y>0:
        #         arcade.set_viewport(pos[0]+cx,pos[1]-cx,pos[2]+cy,pos[3]-cy)
        #     if scroll_y<0:
        #         arcade.set_viewport(pos[0]-cx,pos[1]+cx,pos[2]-cy,pos[3]+cy)

    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.fire = False

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:  # 全屏切换
            self.set_fullscreen(not self.fullscreen)

            width, height = self.get_size()
            self.set_viewport(0, width, 0, height)
        if self.start:

            if key == arcade.key.UP or key == arcade.key.W:
                self.up_pressed = True
            elif key == arcade.key.DOWN or key == arcade.key.S:
                self.down_pressed = True
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.left_pressed = True
            elif key == arcade.key.RIGHT or key == arcade.key.D:
                self.right_pressed = True

    def on_key_release(self, key, modifiers):
        if self.start:
            """Called when the user releases a key. """

            if key == arcade.key.UP or key == arcade.key.W:
                self.up_pressed = False
            elif key == arcade.key.DOWN or key == arcade.key.S:
                self.down_pressed = False
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.left_pressed = False
            elif key == arcade.key.RIGHT or key == arcade.key.D:
                self.right_pressed = False

    # 更新屏幕比例，窗口size变化时自动调用
    def on_resize(self, width, height):

        arcade.set_viewport(self.view_left,
                            self.width + self.view_left,
                            self.view_bottom,
                            self.height + self.view_bottom)
        # print (self.width,self.height)
        # view_pos = self.get_viewport()
        # print(view_pos)

    def update(self, delta_time):
        # super().update(0.1)
        start_time = timeit.default_timer()
        if self.start:

            self.wall_list.update()
            self.bullet_list.update()
            self.bullet_list1.update()
            self.e_bullet_list.update()
            self.enemy_list.update()
            self.tower_list.update()
            self.f_tower_list.update()
            self.t_bullet_list.update()
            self.f_bullet_list.update()
            self.explosions_list.update()
            self.e_b_list.update()
            self.stuff_list.update()
            self.player_sprite.update()
            self.boss_list.update()

            # self.boss_sprite.update()

            # for wall in self.wall_list:
            #     get = arcade.check_for_collision(self.player_sprite, wall)
            #     if get:
            #         print(get)
            # 玩家重生
            if self.player_sprite.blood<=0:
                placed = False
                while not placed:
                    max_x = GRID_WIDTH * SPRITE_SIZE
                    max_y = GRID_HEIGHT * SPRITE_SIZE
                    self.player_sprite.center_x = random.randrange(max_x)
                    self.player_sprite.center_y = random.randrange(max_y)
                    # print(22)

                    # 判断是否与墙冲突
                    walls_hit = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)
                    if len(walls_hit) == 0:
                        placed = True
                self.player_sprite.respawn()
            self.firecount += 1
            # print(self.firecount)
            if self.fire and self.firecount % 10 == 0:
                self.firecount = 1

                bullet = PlayerBullets("files/火箭.png", SPRITE_SCALING, 50 * self.n, 8 * SPRITE_SCALING * 4,
                                       self.e_b_list)

                # Position

                start_x = self.player_sprite.center_x
                start_y = self.player_sprite.center_y
                bullet.center_x = start_x
                bullet.center_y = start_y

                view_pos = self.get_viewport()
                # print(view_pos)
                # print(self.player_sprite.center_x,self.player_sprite.center_y)
                # print (x,y)

                dest_x = self.x + view_pos[0]
                dest_y = self.y + view_pos[2]
                # print(x,y)

                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                # print(x_diff)
                angle = math.atan2(y_diff, x_diff)  # 计算角度 弧度

                self.player_sprite.angle = math.degrees(angle) - 90
                bullet.angle = math.degrees(angle)

                # print(f"Bullet angle: {bullet.angle:.2f}")
                arcade.play_sound(self.gun_sound)

                bullet.change_x = math.cos(angle) * bullet.speed
                bullet.change_y = math.sin(angle) * bullet.speed

                self.bullet_list.append(bullet)
            # 撞墙检查
            hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)
            while hit_list:
                start_x = hit_list[0].center_x
                start_y = hit_list[0].center_y

                dest_x = self.player_sprite.center_x
                dest_y = self.player_sprite.center_y

                x_diff = dest_x - start_x
                y_diff = dest_y - start_y
                angle = math.atan2(y_diff, x_diff)
                # d_angle = math.degrees(angle)
                self.player_sprite.center_x += 2 * math.cos(angle)
                self.player_sprite.center_y += 2 * math.sin(angle)
                hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)

            if self.score > 0:
                self.player_sprite.ATK = self.player_sprite.Damage + self.score / 4
                self.DEF = self.player_sprite.Armor + self.score / 6
            elif self.score < 0:
                self.player_sprite.ATK = self.player_sprite.Damage
                self.DEF = self.player_sprite.Armor

            # self.fscore += self.score
            # 判断是否得到stuff
            get_stuff = arcade.check_for_collision_with_list(self.player_sprite, self.stuff_list)
            if get_stuff:
                self.player_sprite.Armor += get_stuff[0].Armor
                self.player_sprite.Damage += get_stuff[0].Damage
                self.player_sprite.blood += get_stuff[0].HP
                self.player_sprite.Speed += get_stuff[0].Speed
                get_stuff[0].kill()
                self.score += 1
            # 检测英雄子弹
            if len(self.bullet_list):

                for bullet in self.bullet_list:
                    # 检测是否超出视野
                    # if bullet.center_x <= view_pos[0] or bullet.center_x >= view_pos[1] or \
                    #             bullet.center_y <= view_pos[2] or bullet.center_y >= view_pos[3]:
                    #     bullet.kill()
                    # else:
                    # 检测player的子弹是否撞墙
                    bullet_li = arcade.check_for_collision_with_list(bullet, self.wall_list)
                    if bullet_li:
                        bullet.kill()
                        bullet_li[0].blood -= bullet.value + self.player_sprite.ATK
                        bullet_li.clear()
                        # self.score -= 1
                    # 检测player子弹与敌人的碰撞
                    bullet_li1 = arcade.check_for_collision_with_list(bullet, self.enemy_list)
                    if bullet_li1:
                        bullet.kill()
                        bullet_li1[0].blood -= bullet.value + self.player_sprite.ATK
                        bullet_li1.clear()
                        self.score += 1
                    # 检测与boss
                    if len(self.boss_list):
                        bullet_li1 = arcade.check_for_collision(bullet, self.boss_sprite)
                        if bullet_li1:
                            self.boss_sprite.blood -= bullet.value + self.player_sprite.ATK - self.boss_sprite.armor
                            # print((self.boss_sprite.blood))
                            bullet.kill()
                            self.score += 1
            # 英雄跟踪子弹
            if len(self.bullet_list1):
                # view_pos = self.get_viewport()

                for bullet in self.bullet_list1:
                    # 检测是否超出视野
                    if bullet.center_x <= 0 or bullet.center_x >= GRID_WIDTH * SPRITE_SIZE or \
                            bullet.center_y <= 0 or bullet.center_y >= GRID_HEIGHT * SPRITE_SIZE:
                        bullet.kill()
                    # bullet.
                    # else:
                    # # 检测player的子弹是否撞墙
                    # bullet_li = arcade.check_for_collision_with_list(bullet, self.wall_list)
                    # if bullet_li:
                    #     bullet.kill()
                    #     bullet_li[0].blood -= bullet.value + self.player_sprite.ATK
                    #     bullet_li.clear()
                    #     # self.score -= 1
                    # 检测player子弹与敌人的碰撞
                    bullet_li1 = arcade.check_for_collision_with_list(bullet, self.enemy_list)
                    if bullet_li1:
                        bullet.kill()
                        bullet_li1[0].blood -= bullet.value + self.player_sprite.ATK
                        bullet_li1.clear()
                        self.score += 1
                    # 检测与boss
                    if len(self.boss_list):
                        bullet_li1 = arcade.check_for_collision(bullet, self.boss_sprite)
                        if bullet_li1:
                            self.boss_sprite.blood -= bullet.value + self.player_sprite.ATK - self.boss_sprite.armor
                            # print((self.boss_sprite.blood))
                            bullet.kill()
                            self.score += 1
            # 检测敌人子弹
            for e_bullet in self.e_bullet_list:
                # 敌人子弹与墙的碰撞
                e_bullet_li = arcade.check_for_collision_with_list(e_bullet, self.wall_list)
                if e_bullet_li:
                    explosion = Explosion(e_b_texture_list)
                    explosion.center_x = e_bullet_li[0].center_x
                    explosion.center_y = e_bullet_li[0].center_y
                    self.e_b_list.append(explosion)
                    # arcade.sound.play_sound(e_sound)
                    e_bullet_li[0].blood -= e_bullet.value
                    e_bullet.kill()
                    e_bullet_li.clear()
                # 敌人子弹与玩家的碰撞
                e_bullet_li1 = arcade.check_for_collision_with_list(e_bullet, self.player_list)
                if e_bullet_li1:
                    explosion = Explosion(e_b_texture_list)
                    explosion.center_x = e_bullet_li1[0].center_x
                    explosion.center_y = e_bullet_li1[0].center_y
                    self.e_b_list.append(explosion)
                    # arcade.sound.play_sound(e_sound)
                    atk = e_bullet.value - self.DEF
                    if atk > 0:
                        self.player_sprite.blood -= atk
                    e_bullet.kill()
                    self.score -= 1
            # 检测普通炮塔
            for tower in self.tower_list:
                # 检测炮塔与玩家的距离
                t_distance = arcade.get_distance_between_sprites(tower, self.player_sprite)
                if t_distance <= 450:  # 炮塔开火条件
                    tower.fire(self.player_sprite, self.t_bullet_list)
                hit_tower = arcade.check_for_collision_with_list(tower, self.bullet_list)  # 玩家子弹伤害tower
                if hit_tower:
                    tower.blood -= self.bullet_list[0].value + self.player_sprite.ATK
                    hit_tower[0].kill()
                    self.score += 1
                hit_tower = arcade.check_for_collision_with_list(tower, self.bullet_list1)  # 玩家子弹伤害tower
                if hit_tower:
                    tower.blood -= self.bullet_list1[0].value + self.player_sprite.ATK
                    hit_tower[0].kill()
                    self.score += 1
            # 检查跟踪炮塔
            for tower in self.f_tower_list:
                # 检测炮塔与玩家的距离
                ft_distance = arcade.get_distance_between_sprites(tower, self.player_sprite)
                if ft_distance <= 800:  # 炮塔开火条件
                    tower.follow_fire(self.player_sprite, self.f_bullet_list, self.e_b_list)
                hit_tower = arcade.check_for_collision_with_list(tower, self.bullet_list)  # 玩家子弹伤害tower
                if hit_tower:
                    tower.blood -= self.bullet_list[0].value + self.player_sprite.ATK
                    hit_tower[0].kill()
                    self.score += 1
                hit_tower = arcade.check_for_collision_with_list(tower, self.bullet_list1)  # 玩家子弹伤害tower
                if hit_tower:
                    tower.blood -= self.bullet_list1[0].value + self.player_sprite.ATK
                    hit_tower[0].kill()
                    self.score += 1
            # 检查炮塔子弹
            for t_bullet in self.t_bullet_list:
                # 炮塔子弹与墙的碰撞
                t_bullet_list = arcade.check_for_collision_with_list(t_bullet, self.wall_list)
                if t_bullet_list:
                    explosion = Explosion(t_b_texture_list)
                    explosion.center_x = t_bullet_list[0].center_x
                    explosion.center_y = t_bullet_list[0].center_y
                    self.e_b_list.append(explosion)
                    # arcade.sound.play_sound(e_sound)
                    t_bullet_list[0].blood -= t_bullet.value
                    t_bullet.kill()
                    t_bullet_list.clear()
                # 炮塔子弹与玩家的碰撞
                t_bullet_li1 = arcade.check_for_collision_with_list(t_bullet, self.player_list)
                if t_bullet_li1:
                    explosion = Explosion(t_b_texture_list)
                    explosion.center_x = t_bullet_li1[0].center_x
                    explosion.center_y = t_bullet_li1[0].center_y
                    self.e_b_list.append(explosion)
                    # arcade.sound.play_sound(e_sound)
                    atk = t_bullet.value - self.DEF
                    if atk > 0:
                        self.player_sprite.blood -= atk
                    t_bullet.kill()
                    self.score -= 1
            # 检查跟踪导弹
            for f_bullet in self.f_bullet_list:
                # 更新子弹位置飞行方向
                f_bullet.follow_sprite(self.player_sprite)
                # 炮塔子弹与玩家的碰撞
                t_bullet_li1 = arcade.check_for_collision_with_list(f_bullet, self.player_list)
                if t_bullet_li1:
                    explosion = Explosion(m_b_texture_list)
                    explosion.center_x = t_bullet_li1[0].center_x
                    explosion.center_y = t_bullet_li1[0].center_y
                    self.e_b_list.append(explosion)
                    # arcade.sound.play_sound(f_sound)
                    self.player_sprite.blood -= f_bullet.value - self.DEF
                    f_bullet.kill()
                    self.score -= 1
            # 检测敌人
            for enemy in self.enemy_list:
                # 检测敌人与玩家的距离
                e_distance = arcade.get_distance_between_sprites(enemy, self.player_sprite)
                if e_distance <= 300:
                    enemy.follow_sprite(self.player_sprite)

                if e_distance <= 200:  # 敌人开火条件
                    enemy.fire(self.player_sprite, self.e_bullet_list)

                # 敌人与玩家的碰撞
                hit_player = arcade.check_for_collision(enemy, self.player_sprite)
                if hit_player:
                    self.player_sprite.blood -= enemy.blood
                    explosion = Explosion(player_texture_list)
                    explosion.center_x = enemy.center_x
                    explosion.center_y = enemy.center_y
                    self.explosions_list.append(explosion)
                    arcade.sound.play_sound(explosion_sound)
                    enemy.kill()
                # 敌人撞墙
                e_wall_hit = arcade.check_for_collision_with_list(enemy, self.wall_list)
                if e_wall_hit:
                    enemy.change_x *= 0
                    enemy.change_y *= 0
                    e_wall_hit.clear()
            # 检查boss列表
            if len(self.boss_list):  # boss还在
                # boss距离
                b_distance = arcade.get_distance_between_sprites(self.boss_sprite, self.player_sprite)
                if b_distance <= 1800:
                    self.boss_sprite.follow_sprite(self.player_sprite)

                if b_distance <= 800:
                    self.boss_sprite.follow_fire(self.player_sprite, self.f_bullet_list, self.e_b_list)
                    self.boss_sprite.fire2(self.player_sprite, self.f_bullet_list, self.e_b_list)
                if b_distance <= 400:
                    self.boss_sprite.fire(self.player_sprite, self.t_bullet_list)
            else:  # 当前boss已死亡
                self.boss_sprite = Boss(f"files/boss{self.n:02d}.png", SPRITE_SCALING, 50000, 200, MOVEMENT_SPEED / 15,
                                        self.e_b_list)
                # Randomly place the player. If we are in a wall, repeat until we aren't.
                self.score += 50 * self.n
                placed = False
                while not placed:
                    # Randomly position
                    max_x = GRID_WIDTH * SPRITE_SIZE
                    max_y = GRID_HEIGHT * SPRITE_SIZE
                    self.boss_sprite.center_x = random.randrange(max_x)
                    self.boss_sprite.center_y = random.randrange(max_y)
                    distance = arcade.get_distance_between_sprites(self.boss_sprite, self.player_sprite)
                    if distance >= 800:
                        placed = True
                        self.boss_sprite.blood *= self.n
                        self.boss_sprite.armor += 50
                        self.boss_sprite.speed += self.n / 4
                        self.n += 1
                        global E_BULLET_SPEED, ENEMY_DAMAGE, BULLET_SPEED
                        E_BULLET_SPEED += 0.2
                        ENEMY_DAMAGE += 100
                        BULLET_SPEED += 0.2
                        self.player_sprite.max_blood += self.boss_sprite.blood / 10
                        self.player_sprite.blood = self.player_sprite.max_blood
                        self.player_sprite.ATK += 50
                self.boss_list.append(self.boss_sprite)

            # 检查炮塔数量
            if len(self.tower_list) <= int(GRID_HEIGHT * 0.8 / 5):
                self.score += 20
                for u in range(int(GRID_HEIGHT * 0.3 / 5)):
                    tower1 = Tower("files/炮塔.png", SPRITE_SCALING, 10000 * self.n / 2, 500 * self.n / 2, self.e_b_list)
                    tower1_placed_successfully = False

                    # Keep trying until success
                    while not tower1_placed_successfully:
                        # Position the coin
                        tower1.center_x = random.randrange(GRID_WIDTH * SPRITE_SIZE)
                        tower1.center_y = random.randrange(GRID_HEIGHT * SPRITE_SIZE)

                        # See if the coin is hitting a wall
                        wall_hit_list = arcade.check_for_collision_with_list(tower1, self.wall_list)

                        if len(wall_hit_list) == 0:
                            tower1_placed_successfully = True
                    self.tower_list.append(tower1)
            if len(self.f_tower_list) <= int(GRID_HEIGHT * 0.8 / 10):
                self.score += 20
                for u in range(int(GRID_HEIGHT * 0.4 / 10)):
                    tower2 = Tower("files/炮塔2.png", SPRITE_SCALING, 10000, 500, self.e_b_list)
                    tower2_placed_successfully = False

                    # Keep trying until success
                    while not tower2_placed_successfully:
                        # Position the coin
                        tower2.center_x = random.randrange(GRID_WIDTH * SPRITE_SIZE)
                        tower2.center_y = random.randrange(GRID_HEIGHT * SPRITE_SIZE)

                        # See if the coin is hitting a wall
                        wall_hit_list = arcade.check_for_collision_with_list(tower2, self.wall_list)

                        if len(wall_hit_list) == 0:
                            tower2_placed_successfully = True
                    self.f_tower_list.append(tower2)
            # 检查敌人数
            if len(self.enemy_list) <= int(GRID_HEIGHT * 1.2):
                self.score += 20
                for i in range(int(GRID_HEIGHT * 0.5)):

                    enemy = E_Sprite("files/敌人.png", SPRITE_SCALING, 100 * self.n * random.uniform(0.8, 8))

                    # --- IMPORTANT PART ---

                    # Boolean variable if we successfully placed the coin
                    enemy_placed_successfully = False

                    # Keep trying until success
                    while not enemy_placed_successfully:
                        # Position the coin
                        enemy.center_x = random.randrange(GRID_WIDTH * SPRITE_SIZE)
                        enemy.center_y = random.randrange(GRID_HEIGHT * SPRITE_SIZE)

                        # See if the coin is hitting a wall
                        wall_hit_list = arcade.check_for_collision_with_list(enemy, self.wall_list)

                        # See if the coin is hitting another coin
                        enemy_hit_list = arcade.check_for_collision_with_list(enemy, self.enemy_list)

                        if len(wall_hit_list) == 0 and len(enemy_hit_list) == 0:
                            # It is!
                            enemy_placed_successfully = True
                    self.enemy_list.append(enemy)
            # 初始化按键速度为0
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0

            if self.up_pressed and not self.down_pressed:
                self.player_sprite.change_y = self.player_sprite.Speed
            elif self.down_pressed and not self.up_pressed:
                self.player_sprite.change_y = -self.player_sprite.Speed
            if self.left_pressed and not self.right_pressed:
                self.player_sprite.change_x = -self.player_sprite.Speed
            elif self.right_pressed and not self.left_pressed:
                self.player_sprite.change_x = self.player_sprite.Speed

            self.physics_engine.update()

            changed = False

            # Scroll left
            left_bndry = self.view_left + self.width / 2 - SCROLL * 1.5
            if self.player_sprite.left < left_bndry:
                self.view_left -= left_bndry - self.player_sprite.left
                changed = True

            # Scroll right
            right_bndry = self.view_left + self.width / 2 + SCROLL * 1.5
            if self.player_sprite.right > right_bndry:
                self.view_left += self.player_sprite.right - right_bndry
                changed = True

            # Scroll up
            top_bndry = self.view_bottom + self.height / 2 + SCROLL
            if self.player_sprite.top > top_bndry:
                self.view_bottom += self.player_sprite.top - top_bndry
                changed = True

            # Scroll down
            bottom_bndry = self.view_bottom + self.height / 2 - SCROLL
            if self.player_sprite.bottom < bottom_bndry:
                self.view_bottom -= bottom_bndry - self.player_sprite.bottom
                changed = True

            if changed:
                arcade.set_viewport(self.view_left,
                                    self.width + self.view_left,
                                    self.view_bottom,
                                    self.height + self.view_bottom)
        # super().update(0.1)
        # 计算处理时间
        self.zx1.update()

        self.processing_time = timeit.default_timer() - start_time

    def close(self):
        if not self.start:
            self.clear()
            super().close()
            sys.exit()
        else:
            self.set_viewport(0, self.width, 0, self.height)
            # super().clear()
            with open("files/best_score.txt", "r")as best_score:
                score = int(best_score.read())
                if self.score > score:
                    # best_score.
                    best_score = open("files/best_score.txt", "w")
                    best_score.write(str(self.score))
            self.score = 0
            self.startgame()
            # print(11)

        # self.setup()
        # self.__del__()
        # print(111)

        # super().clear()
        # super(MyGame, self).close()
        # main()
        # sys.exit()


#
# white = (255, 255, 255)
# black = (0, 0, 0)
# gray = (128, 128, 128)
# red = (200, 0, 0)
# green = (0, 200, 0)
# bright_red = (255, 0, 0)
# bright_green = (0, 255, 0)
# blue = (0, 0, 255)
# yellow = (255, 247, 200)
# clo = (255, 0, 0)
# SCREEN = pygame.Rect(0, 0, 550, 450)
#
#
# # 游戏开始界面（用pygame）
# class Ui(object):
#     def __init__(self):
#
#         pygame.mixer.init()
#         pygame.mixer.music.load("./files/sound/bgm1.mp3")
#         pygame.mixer.music.play(-1)
#
#         # self.message_diaplay("not a GAME")
#         #
#         # 初始化:窗口,时钟,方法
#         self.screen = pygame.display.set_mode(SCREEN.size)
#         self.screen_rect = self.screen.get_rect()
#         self.clock = pygame.time.Clock()
#         # print(11)
#         self.screen.fill(yellow)
#
#     def change(self):
#         # game = MyGame()
#         game.setup()
#         arcade.run()
#         self.quit()
#
#         # game.setup()
#         # quit()
#         # arcade.close_window()
#         # game_ui = Ui()
#         # game_ui.start_game()
#
#         # self.start_game()
#
#     def quit(self):
#         pygame.quit()
#         sys.exit()
#
#     def change_size(self):
#         global GRID_HEIGHT
#
#         if GRID_HEIGHT <= 800:
#             GRID_HEIGHT += 50
#         #     self.message_diaplay('{}*{}'.format(str(GRID_HEIGHT),str(GRID_HEIGHT)), 20, (380, 210))
#         if GRID_HEIGHT > 800:
#             GRID_HEIGHT = 50
#         font = pygame.font.SysFont("arial", 30)
#         text = font.render(str(GRID_HEIGHT) + '*' + str(GRID_HEIGHT), True, clo)
#         self.screen.blit(text, (350, 215))
#
#     def change_scaling(self):
#         global SPRITE_SCALING
#
#         if SPRITE_SCALING <= 1:
#             SPRITE_SCALING += 0.1
#         #     self.message_diaplay('{}*{}'.format(str(GRID_HEIGHT),str(GRID_HEIGHT)), 20, (380, 210))
#         if SPRITE_SCALING > 1:
#             SPRITE_SCALING = 0.1
#         font = pygame.font.SysFont("arial", 30)
#         text = font.render(str(SPRITE_SCALING), True, clo)
#         self.screen.blit(text, (350, 285))
#         SPRITE_SCALING = float("{:.2f}".format(SPRITE_SCALING))
#
#     def start_game(self):
#
#         # print("游戏开始")
#         while True:
#             self.clock.tick(12)  # 12帧
#             # self.buttons("START", 220, 140, 100, 50, green, bright_green, start)
#             # self.buttons("SIZE", 220, 210, 100, 50, green, bright_green, self.change_size)
#             # self.buttons("SCALING", 220, 280, 100, 50, green, bright_green, start)
#             # self.buttons("Quit", 220, 350, 100, 50, red, bright_red, self.quit)
#             # self.message_diaplay("Not a Game", 100, ((self.screen_rect.width / 2), (self.screen_rect.height / 7)))
#             # self.message_diaplay('version: 0.1.0.0000 Beta', 20,
#             #                      ((self.screen_rect.width*0.8), (self.screen_rect.height*0.25)))
#             #
#             # for event in pygame.event.get():
#             #     if event.type == pygame.QUIT:
#             #         exit()
#             #
#             # self.__event_handler()
#
#             self.__update_()
#             # 更新屏幕
#             pygame.display.update()
#
#     def __event_handler(self):
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 Ui.__gameover()
#
#     @staticmethod
#     def __gameover():
#         print("游戏退出")
#         pygame.quit()
#         exit()
#
#     # def _create_sprites(self):
#     # 背景
#     # bg1 = Background()
#     # bg2 = Background(is_alt=True)
#     # self.back_groud = pygame.sprite.Group(bg1, bg2)
#     # 按钮类
#     def buttons(self, msg, x, y, w, h, clor1, clor2, action=None):
#         mouse = pygame.mouse.get_pos()
#         click = pygame.mouse.get_pressed()
#         if x + w > mouse[0] > x and y + h > mouse[1] > y:
#             pygame.draw.rect(self.screen, clor2, (x, y, w, h))
#             if click[0] == 1 and action != None:
#                 action()
#         else:
#             pygame.draw.rect(self.screen, clor1, (x, y, w, h))
#         small_text = pygame.font.SysFont("arial", 20)
#         text_surface = small_text.render(msg, True, black)
#         text_rect = text_surface.get_rect()
#         text_rect.center = ((x + (w / 2)), (y + (h / 2)))
#         self.screen.blit(text_surface, text_rect)
#
#     def message_diaplay(self, text, size, pos):
#         large_text = pygame.font.SysFont("arial", size)
#         text_surface = large_text.render(text, True, black)
#         text_rect = text_surface.get_rect()
#         text_rect.center = pos
#         self.screen.blit(text_surface, text_rect)
#         pygame.display.update()
#
#     def __update_(self):
#         global SPRITE_SIZE, BULLET_SPEED, E_BULLET_SPEED, MOVEMENT_SPEED
#
#         self.screen.fill(yellow)
#         # self.start_game()
#         # super().__update_()
#         self.buttons("START", 220, 140, 100, 50, green, bright_green, self.change)
#         self.buttons("SIZE", 220, 210, 100, 50, green, bright_green, self.change_size)
#         self.buttons("SCALING", 220, 280, 100, 50, green, bright_green, self.change_scaling)
#         self.buttons("Quit", 220, 350, 100, 50, red, bright_red, self.quit)
#         self.message_diaplay("Not a Game", 100, ((self.screen_rect.width / 2), (self.screen_rect.height / 7)))
#         self.message_diaplay('version: 0.1.4.190917_Beta', 20,
#                              (420, 120))
#         font = pygame.font.SysFont("arial", 30)
#         text = font.render(str(GRID_HEIGHT) + '*' + str(GRID_HEIGHT), True, clo)
#         self.screen.blit(text, (350, 215))
#         font = pygame.font.SysFont("arial", 30)
#         text = font.render(str(SPRITE_SCALING), True, clo)
#         self.screen.blit(text, (350, 285))
#         BULLET_SPEED = 8 * SPRITE_SCALING * 4
#         E_BULLET_SPEED = 10 * SPRITE_SCALING * 3
#
#         MOVEMENT_SPEED = 4 * SPRITE_SCALING * 3.2
#         SPRITE_SIZE = 90 * SPRITE_SCALING

#         # for event in pygame.event.get():
#         #     if event.type == pygame.QUIT:
#         #         exit()
#
#         self.__event_handler()  # pass
#
#
# def start():
#     game = MyGame()
#     game.setup()
#     # print('play')
#     arcade.run()
#     # pygame.quit()
#     # game.setup()
#     # main()


def main():
    # pygame.init()
    # global hit_sound1,explosion_sound,f_sound,e_sound
    # hit_sound1 = arcade.sound.load_sound("files/sound/爆炸2.wav")  # 方块爆炸声
    # explosion_sound = arcade.load_sound("files/sound/爆炸.wav")  # 玩家子弹爆炸
    # f_sound = arcade.load_sound("files/sound/勘探导弹.wav")
    # e_sound = arcade.load_sound("files/sound/被激光击中爆炸.wav")

    window = Mygame()
    window.startgame()
    # menu_view = MenuView()
    # window.show_view(menu_view)
    # game_ui = Ui()
    # game_ui.start_game()
    # global game
    # game = MyGame()
    # game.startgame()
    # game.setup()
    arcade.run()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
