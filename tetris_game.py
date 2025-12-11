"""
Tetris - Final Enhanced Version (with Cheat)

Features:

* 10x20 grid, 7 tetrominoes, full rotation
* Next piece, Hold, Ghost piece
* Soft drop / Hard drop
* Help (suggestion) calculated via heuristic
* Cheat: a button that automatically places the current piece in the best position (rotation + x + y) and locks it
* Restart button
* Clear Game Over when the stack reaches the top

Execution:

* Install Pygame: pip install pygame
* Run: python3 tetris_game.py

Controls:

* Left / Right: move
* Up / Z: rotate clockwise
* X: rotate counter-clockwise
* Down: soft drop
* Space: hard drop
* C: Hold
* Help button: show/hide suggestion
* Cheat button: instantly place the piece in the best spot
* Restart button: restart game
* Q / ESC: quit
  """

import pygame
import random
import sys
from copy import deepcopy

# ------------------------ Configuration ------------------------
CELL_SIZE = 30
COLUMNS = 10
ROWS = 20
SIDE_PANEL = 6 * CELL_SIZE
WIDTH = CELL_SIZE * COLUMNS + SIDE_PANEL
HEIGHT = CELL_SIZE * ROWS
FPS = 60

PALETTE = {
    'bg': (18, 18, 24),
    'grid': (28, 28, 36),
    'outline': (10, 10, 12),
    'panel': (14, 14, 18),
    'text': (230, 230, 230),
}

TETROMINO_COLORS = {
    'I': (102, 204, 255),
    'O': (255, 204, 102),
    'T': (186, 85, 211),
    'S': (102, 255, 153),
    'Z': (255, 102, 102),
    'J': (102, 153, 255),
    'L': (255, 179, 102),
}

TETROMINOS = {
    'I': [
        [(0,1),(1,1),(2,1),(3,1)],
        [(2,0),(2,1),(2,2),(2,3)],
    ],
    'O': [
        [(1,1),(2,1),(1,2),(2,2)],
    ],
    'T': [
        [(1,1),(0,2),(1,2),(2,2)],
        [(1,1),(1,2),(2,1),(1,3)],
        [(0,2),(1,2),(2,2),(1,3)],
        [(1,1),(0,2),(1,2),(1,3)],
    ],
    'S': [
        [(1,1),(2,1),(0,2),(1,2)],
        [(1,1),(1,2),(2,2),(2,3)],
    ],
    'Z': [
        [(0,1),(1,1),(1,2),(2,2)],
        [(2,1),(1,2),(2,2),(1,3)],
    ],
    'J': [
        [(0,1),(0,2),(1,2),(2,2)],
        [(1,1),(2,1),(1,2),(1,3)],
        [(0,2),(1,2),(2,2),(2,3)],
        [(1,1),(1,2),(0,3),(1,3)],
    ],
    'L': [
        [(2,1),(0,2),(1,2),(2,2)],
        [(1,1),(1,2),(1,3),(2,3)],
        [(0,2),(1,2),(2,2),(0,3)],
        [(0,1),(1,1),(1,2),(1,3)],
    ],
}

for k, rots in TETROMINOS.items():
    if len(rots) == 1:
        TETROMINOS[k] = rots * 4
    elif len(rots) == 2:
        TETROMINOS[k] = rots * 2

# ------------------------ Classes ------------------------
class Piece:
    def __init__(self, kind=None):
        self.kind = kind or random.choice(list(TETROMINOS.keys()))
        self.rot = 0
        self.x = COLUMNS // 2 - 2
        self.y = -1

    @property
    def shape(self):
        return TETROMINOS[self.kind][self.rot % len(TETROMINOS[self.kind])]

    def cells(self):
        return [(self.x + cx, self.y + cy) for (cx, cy) in self.shape]

    def rotate(self, direction=1):
        self.rot = (self.rot + direction) % len(TETROMINOS[self.kind])

    def copy(self):
        p = Piece(self.kind)
        p.rot = self.rot
        p.x = self.x
        p.y = self.y
        return p

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines = 0

    def valid(self, piece):
        for (x, y) in piece.cells():
            if x < 0 or x >= COLUMNS:
                return False
            if y >= ROWS:
                return False
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True

    def lock(self, piece):
        for (x, y) in piece.cells():
            if 0 <= y < ROWS and 0 <= x < COLUMNS:
                self.grid[y][x] = piece.kind

        # Game over if piece had blocks above visible area or top row now occupied
        if any(y < 0 for (_, y) in piece.cells()) or any(self.grid[0][x] is not None for x in range(COLUMNS)):
            return 'GAME_OVER'

        cleared = self.clear_lines()
        self.update_score(cleared)
        return None

    def clear_lines(self):
        new_grid = [row for row in self.grid if any(cell is None for cell in row)]
        cleared = ROWS - len(new_grid)
        while len(new_grid) < ROWS:
            new_grid.insert(0, [None for _ in range(COLUMNS)])
        self.grid = new_grid
        self.lines += cleared
        self.level = 1 + self.lines // 10
        return cleared

    def update_score(self, cleared):
        if cleared == 1:
            pts = 40
        elif cleared == 2:
            pts = 100
        elif cleared == 3:
            pts = 300
        elif cleared >= 4:
            pts = 1200
        else:
            pts = 0
        self.score += pts * self.level

    def get_ghost_y(self, piece):
        ghost = piece.copy()
        while self.valid(ghost):
            ghost.y += 1
        ghost.y -= 1
        return ghost.y

# ------------------------ Heuristics & Suggestion ------------------------
def column_heights(grid):
    heights = [0] * COLUMNS
    for x in range(COLUMNS):
        for y in range(ROWS):
            if grid[y][x] is not None:
                heights[x] = ROWS - y
                break
    return heights

def count_holes(grid):
    holes = 0
    for x in range(COLUMNS):
        block_seen = False
        for y in range(ROWS):
            if grid[y][x] is not None:
                block_seen = True
            elif block_seen and grid[y][x] is None:
                holes += 1
    return holes

def simulate_placement(grid, piece):
    temp = [row[:] for row in grid]
    for (x, y) in piece.cells():
        if 0 <= y < ROWS and 0 <= x < COLUMNS:
            temp[y][x] = piece.kind
    cleared = 0
    for row in temp:
        if None not in row:
            cleared += 1
    heights = column_heights(temp)
    agg_height = sum(heights)
    holes = count_holes(temp)
    return cleared, agg_height, holes

def suggest_placement(board, piece):
    best = None
    best_score = -1e9
    for rot in range(4):
        p = piece.copy()
        p.rot = rot
        for x in range(-2, COLUMNS + 2):
            q = p.copy()
            q.x = x
            q.y = -4
            if not board.valid(q):
                continue
            while board.valid(q):
                q.y += 1
            q.y -= 1
            if not board.valid(q):
                continue
            cleared, agg_height, holes = simulate_placement(board.grid, q)
            score = cleared * 100 - agg_height * 1 - holes * 20
            if score > best_score:
                best_score = score
                best = q.copy()
    return best

# ------------------------ Rendering ------------------------
pygame.font.init()
FONT = pygame.font.SysFont('Consolas', 18)
BIG_FONT = pygame.font.SysFont('Consolas', 28, bold=True)
SMALL_FONT = pygame.font.SysFont('Consolas', 14)

HELP_BUTTON = pygame.Rect(WIDTH - 120, HEIGHT - 50, 100, 40)
RESTART_BUTTON = pygame.Rect(WIDTH - 120, HEIGHT - 100, 100, 40)
CHEAT_BUTTON = pygame.Rect(WIDTH - 120, HEIGHT - 150, 100, 40)


def draw_cell(surface, x, y, size, color, outline=False, alpha=None):
    rect = pygame.Rect(x, y, size, size)
    if alpha is not None:
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        s.fill(color + (alpha,))
        surface.blit(s, (x, y))
    else:
        pygame.draw.rect(surface, color, rect)
    if outline:
        pygame.draw.rect(surface, PALETTE['outline'], rect, 2)


def draw_board(surface, board, current_piece, show_suggestion=False, suggestion_piece=None):
    surface.fill(PALETTE['bg'])
    for r in range(ROWS):
        for c in range(COLUMNS):
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, PALETTE['grid'], rect)
            pygame.draw.rect(surface, PALETTE['outline'], rect, 1)
            cell = board.grid[r][c]
            if cell is not None:
                draw_cell(surface, x+2, y+2, CELL_SIZE-4, TETROMINO_COLORS[cell], outline=True)

    if current_piece:
        ghost_y = board.get_ghost_y(current_piece)
        ghost = current_piece.copy()
        ghost.y = ghost_y
        for (x, y) in ghost.cells():
            if y >= 0:
                draw_cell(surface, x*CELL_SIZE+4, y*CELL_SIZE+4, CELL_SIZE-8, TETROMINO_COLORS[ghost.kind], outline=False, alpha=90)

    if show_suggestion and suggestion_piece:
        for (x, y) in suggestion_piece.cells():
            if y >= 0:
                draw_cell(surface, x*CELL_SIZE+2, y*CELL_SIZE+2, CELL_SIZE-4, (200,200,50), outline=True, alpha=120)

    if current_piece:
        for (x, y) in current_piece.cells():
            if y >= 0:
                draw_cell(surface, x*CELL_SIZE+2, y*CELL_SIZE+2, CELL_SIZE-4, TETROMINO_COLORS[current_piece.kind], outline=True)


def draw_side_panel(surface, board, next_piece, hold_piece):
    panel_rect = pygame.Rect(CELL_SIZE * COLUMNS, 0, SIDE_PANEL, HEIGHT)
    pygame.draw.rect(surface, PALETTE['panel'], panel_rect)

    x0 = CELL_SIZE * COLUMNS + 20
    y0 = 20
    surface.blit(BIG_FONT.render('TETRIS+', True, PALETTE['text']), (x0, y0))
    y0 += 50

    surface.blit(FONT.render('Next', True, PALETTE['text']), (x0, y0))
    y0 += 30
    if next_piece:
        draw_mini_piece(surface, next_piece, x0 + 20, y0)
    y0 += 90

    surface.blit(FONT.render('Hold', True, PALETTE['text']), (x0, y0))
    y0 += 30
    if hold_piece:
        draw_mini_piece(surface, hold_piece, x0 + 20, y0)
    y0 += 90

    surface.blit(FONT.render(f'Score: {board.score}', True, PALETTE['text']), (x0, y0))
    y0 += 28
    surface.blit(FONT.render(f'Level: {board.level}', True, PALETTE['text']), (x0, y0))
    y0 += 28
    surface.blit(FONT.render(f'Lines: {board.lines}', True, PALETTE['text']), (x0, y0))

    pygame.draw.rect(surface, (60,60,90), HELP_BUTTON)
    pygame.draw.rect(surface, (20,20,30), HELP_BUTTON, 2)
    surface.blit(SMALL_FONT.render('Aide', True, PALETTE['text']), (HELP_BUTTON.x + 30, HELP_BUTTON.y + 12))

    pygame.draw.rect(surface, (60,60,90), RESTART_BUTTON)
    pygame.draw.rect(surface, (20,20,30), RESTART_BUTTON, 2)
    surface.blit(SMALL_FONT.render('Restart', True, PALETTE['text']), (RESTART_BUTTON.x + 18, RESTART_BUTTON.y + 12))

    pygame.draw.rect(surface, (60,60,90), CHEAT_BUTTON)
    pygame.draw.rect(surface, (20,20,30), CHEAT_BUTTON, 2)
    surface.blit(SMALL_FONT.render('Cheat', True, PALETTE['text']), (CHEAT_BUTTON.x + 30, CHEAT_BUTTON.y + 12))


def draw_mini_piece(surface, piece_kind, sx, sy):
    if piece_kind is None:
        return
    shape = TETROMINOS[piece_kind][0]
    mini = CELL_SIZE // 2
    for (cx, cy) in shape:
        rx = sx + cx * mini
        ry = sy + cy * mini
        draw_cell(surface, rx, ry, mini-2, TETROMINO_COLORS[piece_kind], outline=True)

# ------------------------ Game Loop ------------------------

def spawn_piece(bag):
    if not bag:
        bag.extend(random.sample(list(TETROMINOS.keys()), len(TETROMINOS)))
    kind = bag.pop(0)
    return Piece(kind)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Tetris v3 - Finale')
    clock = pygame.time.Clock()

    board = Board()
    bag = []
    current = spawn_piece(bag)
    next_piece = spawn_piece(bag)
    hold = None
    can_hold = True

    drop_counter = 0.0
    soft_drop = False
    running = True
    show_suggestion = False
    suggestion_piece = None

    while running:
        dt = clock.tick(FPS) / 1000.0
        drop_counter += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_LEFT:
                    candidate = current.copy()
                    candidate.x -= 1
                    if board.valid(candidate):
                        current.x -= 1
                elif event.key == pygame.K_RIGHT:
                    candidate = current.copy()
                    candidate.x += 1
                    if board.valid(candidate):
                        current.x += 1
                elif event.key in (pygame.K_UP, pygame.K_z):
                    candidate = current.copy()
                    candidate.rotate(1)
                    if board.valid(candidate):
                        current.rotate(1)
                elif event.key == pygame.K_x:
                    candidate = current.copy()
                    candidate.rotate(-1)
                    if board.valid(candidate):
                        current.rotate(-1)
                elif event.key == pygame.K_DOWN:
                    soft_drop = True
                elif event.key == pygame.K_SPACE:
                    while True:
                        candidate = current.copy()
                        candidate.y += 1
                        if not board.valid(candidate):
                            break
                        current.y += 1
                    res = board.lock(current)
                    if res == 'GAME_OVER':
                        game_over_screen(screen, board)
                        return
                    current = next_piece
                    next_piece = spawn_piece(bag)
                    can_hold = True
                elif event.key == pygame.K_c:
                    if can_hold:
                        if hold is None:
                            hold = Piece(current.kind)
                            current = next_piece
                            next_piece = spawn_piece(bag)
                        else:
                            hold.kind, current.kind = current.kind, hold.kind
                            current.x = COLUMNS // 2 - 2
                            current.y = -1
                        can_hold = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    soft_drop = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if HELP_BUTTON.collidepoint(mx, my):
                    show_suggestion = not show_suggestion
                    suggestion_piece = suggest_placement(board, current) if show_suggestion else None
                if RESTART_BUTTON.collidepoint(mx, my):
                    main()
                    return
                if CHEAT_BUTTON.collidepoint(mx, my):
                    # Cheat: find the best placement and lock the piece instantly
                    best = suggest_placement(board, current)
                    if best:
                        # place current exactly as best and lock
                        current.x = best.x
                        current.y = best.y
                        current.rot = best.rot
                        res = board.lock(current)
                        if res == 'GAME_OVER':
                            game_over_screen(screen, board)
                            return
                        current = next_piece
                        next_piece = spawn_piece(bag)
                        can_hold = True
                        suggestion_piece = suggest_placement(board, current) if show_suggestion else None

        # gravity
        if soft_drop:
            interval = 0.02
        else:
            interval = max(0.02, 0.8 - (board.level - 1) * 0.07)

        if drop_counter >= interval:
            drop_counter = 0
            candidate = current.copy()
            candidate.y += 1
            if board.valid(candidate):
                current.y += 1
            else:
                res = board.lock(current)
                if res == 'GAME_OVER':
                    game_over_screen(screen, board)
                    return
                current = next_piece
                next_piece = spawn_piece(bag)
                can_hold = True
                if show_suggestion:
                    suggestion_piece = suggest_placement(board, current)

        draw_board(screen, board, current, show_suggestion, suggestion_piece)
        draw_side_panel(screen, board, next_piece.kind if next_piece else None, hold.kind if hold else None)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# ------------------------ Game Over ------------------------

def game_over_screen(surface, board):
    pygame.font.init()
    go_font = pygame.font.SysFont('Consolas', 36, bold=True)
    small = pygame.font.SysFont('Consolas', 20)
    surface.fill(PALETTE['bg'])
    txt = go_font.render('GAME OVER', True, PALETTE['text'])
    surface.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 60))
    sc = small.render(f'Score: {board.score}  Lines: {board.lines}', True, PALETTE['text'])
    surface.blit(sc, (WIDTH//2 - sc.get_width()//2, HEIGHT//2))
    pygame.display.flip()
    pygame.time.wait(2500)

# ------------------------ Entrypoint ------------------------
if __name__ == '__main__':
    main()
