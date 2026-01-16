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
MAX_JUMP_X = 180  # jarak horizontal maksimal
MIN_GAP_X = 40  # biar gak nempel


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


def draw(window, background, bg_image, player, objects):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window)

    player.draw(window)
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
    player.move(dx, 0)
    player.update()
    collided_objects = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_objects = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_objects


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

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
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        self.fall_count += 1
        self.update_sprite()

    def draw(self, win):
        win.blit(self.sprite, (self.rect.x, self.rect.y))

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

    def draw(self, win):
        win.blit(self.image, (self.rect.x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


def generate_vertical_level(start_y, count, block_size, last_center_x, last_dir=None):
    platforms = []
    current_y = start_y

    if last_dir is None:
        last_dir = random.choice([-1, 1])

    MIN_DY = block_size * 1
    MAX_DY = block_size * 2

    for _ in range(count):
        length = random.choice([1, 2, 3])
        platform_width = length * block_size
        half = platform_width // 2

        # naik Y (selalu masuk akal buat lompat)
        dy = random.randint(MIN_DY, MAX_DY)
        current_y -= dy

        # pilih arah tapi BATASI jarak lompat
        direction = -last_dir if random.random() < 0.35 else last_dir

        max_dx = min(MAX_JUMP_X, block_size * 3)
        dx = random.randint(block_size, max_dx) * direction

        center_x = last_center_x + dx

        # clamp layar
        center_x = max(half + 20, min(WIDTH - half - 20, center_x))

        # FINAL ANTI VERTICAL STACK
        if abs(center_x - last_center_x) < block_size * 1.5:
            center_x += block_size * direction

        left_x = center_x - half

        for i in range(length):
            platforms.append(Block(left_x + i * block_size, current_y, block_size))

        last_center_x = center_x
        last_dir = direction

    return platforms, last_center_x, last_dir


def generate_floor(y, block_size):
    floor = []
    for x in range(0, WIDTH, block_size):
        floor.append(Block(x, y, block_size))
    return floor


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(WIDTH // 2, HEIGHT - 120, 50, 50)

    objects = []
    last_dir = None

    floor = generate_floor(HEIGHT - block_size, block_size)
    objects.extend(floor)

    highest = min(objects, key=lambda o: o.rect.y)
    last_x = highest.rect.centerx

    platforms, last_x, last_dir = generate_vertical_level(
        start_y=highest.rect.y,
        count=10,
        block_size=block_size,
        last_center_x=last_x,
        last_dir=last_dir,
    )
    objects.extend(platforms)

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        handle_move(player, objects)
        if player.rect.top <= HEIGHT // 3:
            diff = HEIGHT // 3 - player.rect.top
            player.rect.top = HEIGHT // 3

            for obj in objects:
                obj.rect.y += diff

        draw(window, background, bg_image, player, objects)
        objects = [o for o in objects if o.rect.top < HEIGHT + 100]

        if len(objects) < 40:
            highest = min(objects, key=lambda o: o.rect.y)
            new_platforms, last_x, last_dir = generate_vertical_level(
                start_y=highest.rect.y,
                count=10,
                block_size=block_size,
                last_center_x=last_x,
                last_dir=last_dir,
            )
            objects.extend(new_platforms)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
