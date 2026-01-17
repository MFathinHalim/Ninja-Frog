import math
import os
import random
from os import listdir
from os.path import isfile, join

import pygame

pygame.init()

pygame.display.set_caption("Game Fathin")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
MAX_JUMP_X = 180
MIN_GAP_X = 40


window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = [i * width, j * height]
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)
    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

        collided_objects.append(obj)

    return collided_objects


def handle_move(player, objects):
    keys = pygame.key.get_pressed()
    player.on_wall = False
    player.wall_dir = None
    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(PLAYER_VEL)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(PLAYER_VEL)

    handle_vertical_collision(player, objects, player.y_vel)


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


def collide(player, objects, dx):
    player.rect.x += dx
    collided_object = None

    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            player.on_wall = True
            player.wall_dir = "left" if dx < 0 else "right"
            break

    player.rect.x -= dx
    return collided_object


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3
    WALL_JUMP_X = 8
    WALL_JUMP_Y = 10

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.on_wall = False
        self.wall_stick = False
        self.wall_dir = None

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def wall_jump(self):
        if not self.wall_stick or not self.wall_dir:
            return
        # lompat menjauh dari wall
        if self.wall_dir == "left":
            self.x_vel = self.WALL_JUMP_X
            self.direction = "right"
        elif self.wall_dir == "right":
            self.x_vel = -self.WALL_JUMP_X
            self.direction = "left"

        self.y_vel = -self.WALL_JUMP_Y
        self.wall_stick = False
        self.fall_count = 0
        self.jump_count = 1

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.wallStick()

        if not self.wall_stick:
            self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
            self.fall_count += 1
        else:
            self.y_vel = 0
            self.fall_count = 0

        self.move(self.x_vel, self.y_vel)
        self.wallStick()
        self.update_sprite()

    def wallStick(self):
        keys = pygame.key.get_pressed()
        self.wall_stick = False

        if self.y_vel < 0:
            return  # lagi naik, gak boleh nempel

        if self.wall_dir == "left" and keys[pygame.K_a]:
            self.wall_stick = True
        elif self.wall_dir == "right" and keys[pygame.K_d]:
            self.wall_stick = True

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            # elif self.jump_count == 2:
            #    sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        if self.wall_stick:
            if self.wall_dir == "left":
                self.direction = "right"
            elif self.wall_dir == "right":
                self.direction = "left"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


def generate_floor(y, block_size):
    floor = []
    for x in range(0, WIDTH, block_size):
        floor.append(Block(x, y, block_size))
    return floor


def load_level_from_text(path, block_size):
    platforms = []
    player_spawn = [0, 0]

    with open(path, "r") as f:
        lines = f.read().splitlines()

    for row_index, line in enumerate(lines):
        for col_index, char in enumerate(line):
            x = col_index * block_size
            y = row_index * block_size
            if char == "M":
                platforms.append(Block(x, y, block_size))
            elif char == "P":
                player_spawn = [x, y]

    return platforms, player_spawn


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    objects = []

    level_platforms, player_spawn = load_level_from_text(
        "levels/level1.txt", block_size
    )
    player = Player(player_spawn[0], player_spawn[1] - 50, 50, 50)

    objects.extend(level_platforms)

    offset_x = 0

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if player.wall_stick:
                        player.wall_jump()
                    elif player.jump_count < 2:
                        player.jump()
        player.loop(FPS)
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)
        target_offset_x = player.rect.centerx - WIDTH // 2
        offset_x += (target_offset_x - offset_x) * 0.1
        objects = [o for o in objects if o.rect.top < HEIGHT + 100]

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
