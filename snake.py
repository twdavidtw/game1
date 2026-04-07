import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
BLOCK_SIZE = 20
FPS = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

class Snake:
    def __init__(self):
        self.length = 1
        self.positions = [(WIDTH // 2, HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.color = GREEN
        self.score = 0

    def get_head_position(self):
        return self.positions[0]

    def turn(self, point):
        if self.length > 1 and (point[0] * -1, point[1] * -1) == self.direction:
            return
        else:
            self.direction = point

    def move(self):
        cur = self.get_head_position()
        x, y = self.direction
        new = (
            (cur[0] + (x * BLOCK_SIZE)) % WIDTH,
            (cur[1] + (y * BLOCK_SIZE)) % HEIGHT,
        )
        if len(self.positions) > 2 and new in self.positions[2:]:
            self.reset()
        else:
            self.positions.insert(0, new)
            if len(self.positions) > self.length:
                self.positions.pop()

    def reset(self):
        self.length = 1
        self.positions = [(WIDTH // 2, HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.score = 0

    def draw(self, surface):
        for p in self.positions:
            r = pygame.Rect((p[0], p[1]), (BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(surface, self.color, r)
            pygame.draw.rect(surface, BLACK, r, 1)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()

    def randomize_position(self):
        self.position = (
            random.randint(0, (WIDTH // BLOCK_SIZE) - 1) * BLOCK_SIZE,
            random.randint(0, (HEIGHT // BLOCK_SIZE) - 1) * BLOCK_SIZE,
        )

    def draw(self, surface):
        r = pygame.Rect((self.position[0], self.position[1]), (BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.rect(surface, self.color, r)
        pygame.draw.rect(surface, BLACK, r, 1)

def draw_grid(surface):
    for y in range(0, HEIGHT, BLOCK_SIZE):
        for x in range(0, WIDTH, BLOCK_SIZE):
            r = pygame.Rect((x, y), (BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(surface, (40, 40, 40), r, 1)

import os

# New function to handle file path resolution for PyInstaller
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    # Initialize mixer for sound
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("貪食蛇遊戲")
    clock = pygame.time.Clock()

    snake = Snake()
    food = Food()

    # Try to find a Chinese font
    font_name = pygame.font.match_font('microsoftyahei', 'simhei', 'arial')
    font = pygame.font.Font(font_name, 24)
    
    # Large background font
    bg_font = pygame.font.Font(font_name, 100)
    bg_text = bg_font.render("VICTOR GAME", True, WHITE)
    bg_rect = bg_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    # Load sounds
    score_sound = pygame.mixer.Sound(resource_path("score.wav"))
    pygame.mixer.music.load(resource_path("background.wav"))
    pygame.mixer.music.play(-1) # Loop forever

    while True:
        screen.fill(BLACK)
        draw_grid(screen)
        screen.blit(bg_text, bg_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.turn(UP)
                elif event.key == pygame.K_DOWN:
                    snake.turn(DOWN)
                elif event.key == pygame.K_LEFT:
                    snake.turn(LEFT)
                elif event.key == pygame.K_RIGHT:
                    snake.turn(RIGHT)

        snake.move()
        if snake.get_head_position() == food.position:
            snake.length += 1
            snake.score += 1
            score_sound.play() # Play score sound
            food.randomize_position()

        snake.draw(screen)
        food.draw(screen)

        score_text = font.render(f"得分: {snake.score}", True, WHITE)
        screen.blit(score_text, (5, 5))

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
