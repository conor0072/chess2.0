# Conor Kelly
# June, 13, 2025 
# Please read the READ.ME

import pygame
import random
from stockfish import Stockfish

# Initialize Pygame
pygame.init()

# Set up display
width, height = 600, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Chess Game")

# Define colors
light_square = (240, 217, 181)
dark_square = (181, 136, 99)
popup_bg = (255, 255, 255)

# Load images
pieces = {
    "b_pawn": pygame.image.load("assets/b_pawn.png"),
    "b_rook": pygame.image.load("assets/b_rook.png"),
    "b_knight": pygame.image.load("assets/b_knight.png"),
    "b_bishop": pygame.image.load("assets/b_bishop.png"),
    "b_queen": pygame.image.load("assets/b_queen.png"),
    "b_king": pygame.image.load("assets/b_king.png"),
    "w_pawn": pygame.image.load("assets/w_pawn.png"),
    "w_rook": pygame.image.load("assets/w_rook.png"),
    "w_knight": pygame.image.load("assets/w_knight.png"),
    "w_bishop": pygame.image.load("assets/w_bishop.png"),
    "w_queen": pygame.image.load("assets/w_queen.png"),
    "w_king": pygame.image.load("assets/w_king.png"),
}

# Initialize board template
initial_board = [
    ["b_rook", "b_knight", "b_bishop", "b_queen", "b_king", "b_bishop", "b_knight", "b_rook"],
    ["b_pawn", "b_pawn", "b_pawn", "b_pawn", "b_pawn", "b_pawn", "b_pawn", "b_pawn"],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["w_pawn", "w_pawn", "w_pawn", "w_pawn", "w_pawn", "w_pawn", "w_pawn", "w_pawn"],
    ["w_rook", "w_knight", "w_bishop", "w_queen", "w_king", "w_bishop", "w_knight", "w_rook"]
]

starting_board = [row[:] for row in initial_board]

selected_piece = None
selected_pos = None
dragging = False
turn = 'w'
legal_moves = []
game_over = False
last_move = None
font = pygame.font.Font(None, 48)


class Button:
    """Simple UI button."""

    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, surface):
        pygame.draw.rect(surface, (70, 70, 70), self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)
        label = font.render(self.text, True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class StockfishAI:
    """Wrap Stockfish engine with difficulty presets."""

    LEVELS = {
        "easy": {"depth": 4, "skill": 5},
        "medium": {"depth": 8, "skill": 10},
        "hard": {"depth": 15, "skill": 20},
    }

    def __init__(self, path="stockfish/stockfish-macos-x86-64-avx2", level="easy"):
        params = self.LEVELS.get(level, self.LEVELS["easy"])
        self.engine = Stockfish(path=path, depth=params["depth"], parameters={"Skill Level": params["skill"]})

    def best_move(self, fen):
        try:
            self.engine.set_fen_position(fen)
            return self.engine.get_best_move()
        except Exception:
            return None

# Castling state flags
castle_rights = {
    'w_kingside': True,
    'w_queenside': True,
    'b_kingside': True,
    'b_queenside': True,
}

def is_path_clear(board, squares):
    """Return True if all squares are empty."""
    for r, c in squares:
        if board[r][c] != "":
            return False
    return True


def is_castle_path_safe(board, color, squares):
    """Check that the king does not pass through check when castling."""
    king_pos = find_king(board, color)
    if not king_pos:
        return False
    kr, kc = king_pos
    for r, c in squares:
        backup = board[r][c]
        board[kr][kc] = ""
        board[r][c] = f"{color}_king"
        safe = not is_king_in_check(board, color)
        board[r][c] = backup
        board[kr][kc] = f"{color}_king"
        if not safe:
            return False
    return True


def is_valid_move(board, piece, start_pos, end_pos, check_castle=True):
    sr, sc = start_pos
    er, ec = end_pos
    dr, dc = er - sr, ec - sc

    if sr == er and sc == ec:
        return False

    target = board[er][ec]
    if target and target[0] == piece[0]:
        return False

    kind = piece[2:]

    if kind == "pawn":
        direction = -1 if piece.startswith("w") else 1
        start_row = 6 if piece.startswith("w") else 1

        if sc == ec:
            if dr == direction and board[er][ec] == "":
                return True
            if sr == start_row and dr == 2 * direction and board[sr + direction][sc] == "" and board[er][ec] == "":
                return True
        elif abs(sc - ec) == 1 and dr == direction and board[er][ec] != "":
            return True

    elif kind == "rook":
        if sr == er or sc == ec:
            if sr == er:
                step = 1 if ec > sc else -1
                for c in range(sc + step, ec, step):
                    if board[sr][c] != "":
                        return False
            else:
                step = 1 if er > sr else -1
                for r in range(sr + step, er, step):
                    if board[r][sc] != "":
                        return False
            return True

    elif kind == "knight":
        return (abs(dr), abs(dc)) in [(2, 1), (1, 2)]

    elif kind == "bishop":
        if abs(dr) == abs(dc):
            r_step = 1 if dr > 0 else -1
            c_step = 1 if dc > 0 else -1
            for i in range(1, abs(dr)):
                if board[sr + i * r_step][sc + i * c_step] != "":
                    return False
            return True

    elif kind == "queen":
        return (
            is_valid_move(board, piece[0] + "_rook", start_pos, end_pos, check_castle)
            or is_valid_move(board, piece[0] + "_bishop", start_pos, end_pos, check_castle)
        )

    elif kind == "king":
        if max(abs(dr), abs(dc)) == 1:
            return True
        # Castling logic
        color = piece[0]
        if check_castle and not is_king_in_check(board, color):
            if color == 'w' and sr == 7 and sc == 4 and er == 7:
                # White castling
                if ec == 6 and castle_rights['w_kingside']:
                    path = [(7,5), (7,6)]
                    return is_path_clear(board, path) and is_castle_path_safe(board, color, path)
                if ec == 2 and castle_rights['w_queenside']:
                    path = [(7,3), (7,2)]
                    return is_path_clear(board, [(7,1), (7,2), (7,3)]) and is_castle_path_safe(board, color, path)
            elif color == 'b' and sr == 0 and sc == 4 and er == 0:
                # Black castling
                if ec == 6 and castle_rights['b_kingside']:
                    path = [(0,5), (0,6)]
                    return is_path_clear(board, path) and is_castle_path_safe(board, color, path)
                if ec == 2 and castle_rights['b_queenside']:
                    path = [(0,3), (0,2)]
                    return is_path_clear(board, [(0,1), (0,2), (0,3)]) and is_castle_path_safe(board, color, path)

    return False

def is_king_in_check(board, color):
    king_pos = None
    for row in range(8):
        for col in range(8):
            if board[row][col] == color + "_king":
                king_pos = (row, col)
    if not king_pos:
        return True

    opponent_color = 'b' if color == 'w' else 'w'
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece[0] == opponent_color:
                if is_valid_move(board, piece, (row, col), king_pos, False):
                    return True
    return False

def find_king(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c] == f"{color}_king":
                return (r, c)
    return None


def board_to_fen(board, turn, rights):
    mapping = {
        "w_pawn": "P",
        "w_rook": "R",
        "w_knight": "N",
        "w_bishop": "B",
        "w_queen": "Q",
        "w_king": "K",
        "b_pawn": "p",
        "b_rook": "r",
        "b_knight": "n",
        "b_bishop": "b",
        "b_queen": "q",
        "b_king": "k",
    }
    rows = []
    for row in board:
        empty = 0
        fen_row = ""
        for cell in row:
            if cell == "":
                empty += 1
            else:
                if empty:
                    fen_row += str(empty)
                    empty = 0
                fen_row += mapping[cell]
        if empty:
            fen_row += str(empty)
        rows.append(fen_row)
    fen = "/".join(rows)
    fen += f" {'w' if turn == 'w' else 'b'} "
    castle = ""
    if rights['w_kingside']:
        castle += "K"
    if rights['w_queenside']:
        castle += "Q"
    if rights['b_kingside']:
        castle += "k"
    if rights['b_queenside']:
        castle += "q"
    if castle == "":
        castle = "-"
    fen += castle + " - 0 1"
    return fen


def parse_uci_move(move):
    sr = 8 - int(move[1])
    sc = ord(move[0]) - 97
    er = 8 - int(move[3])
    ec = ord(move[2]) - 97
    promotion = move[4] if len(move) == 5 else None
    return (sr, sc), (er, ec), promotion

def generate_legal_moves(board, piece, start_pos):
    moves = []
    sr, sc = start_pos
    for r in range(8):
        for c in range(8):
            if is_valid_move(board, piece, start_pos, (r, c)):
                backup = board[r][c]
                board[r][c] = piece
                board[sr][sc] = ""
                rook_move = None
                if piece.endswith("king") and abs(c - sc) == 2:
                    row = 7 if piece.startswith('w') else 0
                    if c == 6:
                        rook_move = ((row, 7), (row, 5))
                    elif c == 2:
                        rook_move = ((row, 0), (row, 3))
                    if rook_move:
                        r_start, r_end = rook_move
                        board[r_end[0]][r_end[1]] = board[r_start[0]][r_start[1]]
                        board[r_start[0]][r_start[1]] = ""
                if not is_king_in_check(board, piece[0]):
                    moves.append((r, c))
                board[sr][sc] = piece
                board[r][c] = backup
                if rook_move:
                    board[rook_move[0][0]][rook_move[0][1]] = board[rook_move[1][0]][rook_move[1][1]]
                    board[rook_move[1][0]][rook_move[1][1]] = ""
    return moves

def is_checkmate(board, color):
    if not is_king_in_check(board, color):
        return False
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece[0] == color:
                if generate_legal_moves(board, piece, (r, c)):
                    return False
    return True

def promote_pawn(piece):
    color = piece[0]
    selecting = True
    options = ["queen", "rook", "bishop", "knight"]
    buttons = []
    square_size = width // 8

    draw_board(screen)
    popup_width = len(options) * (square_size + 20) + 20
    popup_height = square_size + 40
    popup_rect = pygame.Rect((width - popup_width) // 2, (height - popup_height) // 2, popup_width, popup_height)
    pygame.draw.rect(screen, popup_bg, popup_rect, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), popup_rect, 2, border_radius=10)

    for i, name in enumerate(options):
        rect = pygame.Rect(popup_rect.x + 20 + i * (square_size + 20), popup_rect.y + 20, square_size, square_size)
        img = pygame.transform.smoothscale(pieces[color + "_" + name], (square_size, square_size))
        pygame.draw.rect(screen, (220, 220, 220), rect)
        screen.blit(img, rect.topleft)
        buttons.append((rect, color + "_" + name))

    pygame.display.flip()

    while selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for rect, result in buttons:
                    if rect.collidepoint(mx, my):
                        selecting = False
                        return result
    return color + "_queen"

def draw_board(surface, board=None):
    if board is None:
        board = starting_board
    square_size = width // 8
    for row in range(8):
        for col in range(8):
            color = light_square if (row + col) % 2 == 0 else dark_square
            rect = pygame.Rect(col * square_size, row * square_size, square_size, square_size)
            pygame.draw.rect(surface, color, rect)

            if last_move and ((row, col) == last_move[0] or (row, col) == last_move[1]):
                overlay = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                overlay.fill((255, 255, 0, 80))
                surface.blit(overlay, rect.topleft)

            if selected_piece and selected_pos == (row, col):
                overlay = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                overlay.fill((255, 255, 0, 120))
                surface.blit(overlay, rect.topleft)

            if (row, col) in legal_moves:
                overlay = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                overlay.fill((255, 255, 255, 100))
                surface.blit(overlay, rect.topleft)


            piece = board[row][col]
            if piece and (not dragging or (row, col) != selected_pos or board is not starting_board):
                image = pygame.transform.smoothscale(pieces[piece], (square_size, square_size))
                surface.blit(image, (col * square_size, row * square_size))

    # Highlight kings in check
    for color in ('w', 'b'):
        if is_king_in_check(starting_board, color):
            kp = find_king(starting_board, color)
            if kp:
                rect = pygame.Rect(kp[1] * square_size, kp[0] * square_size, square_size, square_size)
                overlay = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 100))
                surface.blit(overlay, rect.topleft)

def update_castle_rights(piece, start_pos):
    """Update castle rights when a king or rook moves."""
    global castle_rights
    sr, sc = start_pos
    if piece == 'w_king':
        castle_rights['w_kingside'] = False
        castle_rights['w_queenside'] = False
    elif piece == 'b_king':
        castle_rights['b_kingside'] = False
        castle_rights['b_queenside'] = False
    elif piece == 'w_rook':
        if sr == 7 and sc == 0:
            castle_rights['w_queenside'] = False
        elif sr == 7 and sc == 7:
            castle_rights['w_kingside'] = False
    elif piece == 'b_rook':
        if sr == 0 and sc == 0:
            castle_rights['b_queenside'] = False
        elif sr == 0 and sc == 7:
            castle_rights['b_kingside'] = False

def animate_move(piece, start_pos, end_pos):
    """Animate a piece moving from start_pos to end_pos."""
    sr, sc = start_pos
    er, ec = end_pos
    square_size = width // 8
    steps = 8
    temp_board = [row[:] for row in starting_board]
    temp_board[sr][sc] = ""
    for i in range(1, steps + 1):
        draw_board(screen, temp_board)
        x = (sc + (ec - sc) * i / steps) * square_size
        y = (sr + (er - sr) * i / steps) * square_size
        img = pygame.transform.smoothscale(pieces[piece], (square_size, square_size))
        screen.blit(img, (x, y))
        pygame.display.flip()
        pygame.time.delay(30)


def reset_game():
    """Reset all global game state."""
    global starting_board, selected_piece, selected_pos, dragging, turn, legal_moves, game_over, last_move, castle_rights
    starting_board = [row[:] for row in initial_board]
    selected_piece = None
    selected_pos = None
    dragging = False
    turn = 'w'
    legal_moves = []
    game_over = False
    last_move = None
    castle_rights = {
        'w_kingside': True,
        'w_queenside': True,
        'b_kingside': True,
        'b_queenside': True,
    }


def draw_button(rect, text):
    """Deprecated helper for drawing buttons."""
    pygame.draw.rect(screen, (70, 70, 70), rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
    label = font.render(text, True, (255, 255, 255))
    screen.blit(label, label.get_rect(center=rect.center))


def show_home_screen():
    """Display the home screen and return selected mode."""
    title_font = pygame.font.Font(None, 72)
    buttons = [
        Button((width // 2 - 120, height // 2 - 100, 240, 50), "AI Easy"),
        Button((width // 2 - 120, height // 2 - 30, 240, 50), "AI Medium"),
        Button((width // 2 - 120, height // 2 + 40, 240, 50), "AI Hard"),
        Button((width // 2 - 120, height // 2 + 110, 240, 50), "Multiplayer"),
        Button((width // 2 - 120, height // 2 + 180, 240, 50), "Exit"),
    ]
    while True:
        draw_board(screen, initial_board)
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        title_surf = title_font.render("Chess", True, (255, 255, 255))
        screen.blit(title_surf, title_surf.get_rect(center=(width // 2, height // 4)))
        for b in buttons:
            b.draw(screen)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i, b in enumerate(buttons):
                    if b.is_clicked((mx, my)):
                        if i == 0:
                            return 'ai_easy'
                        if i == 1:
                            return 'ai_medium'
                        if i == 2:
                            return 'ai_hard'
                        if i == 3:
                            return 'multi'
                        if i == 4:
                            pygame.quit()
                            exit()


def show_win_screen(winner):
    board_img = screen.copy()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    win_font = pygame.font.Font(None, 72)
    text = win_font.render(f"{winner} wins!", True, (255, 255, 255))
    info = font.render("Click anywhere to return home", True, (255, 255, 255))
    board_img.blit(overlay, (0, 0))
    board_img.blit(text, text.get_rect(center=(width // 2, height // 2 - 20)))
    board_img.blit(info, info.get_rect(center=(width // 2, height // 2 + 40)))
    screen.blit(board_img, (0, 0))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
        pygame.time.delay(100)
    reset_game()


def confirm_exit():
    """Display a popup asking if the user wants to quit to the home screen."""
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    yes_btn = Button((width // 2 - 110, height // 2 + 20, 100, 40), "Yes")
    no_btn = Button((width // 2 + 10, height // 2 + 20, 100, 40), "No")
    draw_board(screen)
    screen.blit(overlay, (0, 0))
    msg = font.render("Return to home?", True, (255, 255, 255))
    screen.blit(msg, msg.get_rect(center=(width // 2, height // 2 - 20)))
    yes_btn.draw(screen)
    no_btn.draw(screen)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if yes_btn.is_clicked((mx, my)):
                    return True
                if no_btn.is_clicked((mx, my)):
                    return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_y, pygame.K_RETURN):
                    return True
                if event.key in (pygame.K_n, pygame.K_ESCAPE):
                    return False
        pygame.time.delay(100)


def ai_make_move(color):
    global turn, last_move
    moves = []
    for r in range(8):
        for c in range(8):
            piece = starting_board[r][c]
            if piece and piece[0] == color:
                for move in generate_legal_moves(starting_board, piece, (r, c)):
                    moves.append(((r, c), move))
    if not moves:
        return
    start, end = random.choice(moves)
    piece = starting_board[start[0]][start[1]]
    animate_move(piece, start, end)
    backup_piece = starting_board[end[0]][end[1]]
    starting_board[end[0]][end[1]] = piece
    starting_board[start[0]][start[1]] = ""
    if piece.endswith("king") and abs(end[1] - start[1]) == 2:
        if end[1] == 6:
            starting_board[end[0]][5] = starting_board[end[0]][7]
            starting_board[end[0]][7] = ""
        elif end[1] == 2:
            starting_board[end[0]][3] = starting_board[end[0]][0]
            starting_board[end[0]][0] = ""
    if piece.endswith("pawn") and (end[0] == 0 or end[0] == 7):
        starting_board[end[0]][end[1]] = promote_pawn(piece)
    update_castle_rights(piece, start)
    last_move = (start, end)
    turn = 'b' if turn == 'w' else 'w'


def game_loop(vs_ai=False, difficulty="easy"):
    reset_game()
    ai_color = 'b' if vs_ai else None
    ai_engine = StockfishAI(level=difficulty) if vs_ai else None
    running = True
    global dragging, selected_piece, selected_pos, legal_moves, turn, game_over
    while running:
        screen.fill((0, 0, 0))
        draw_board(screen)

        square_size = width // 8
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_col = mouse_x // square_size
        mouse_row = mouse_y // square_size

        if vs_ai and turn == ai_color and not game_over:
            fen = board_to_fen(starting_board, turn, castle_rights)
            move = ai_engine.best_move(fen)
            if not move:
                ai_make_move(ai_color)
            else:
                (s_pos, e_pos, promo) = parse_uci_move(move)
                piece = starting_board[s_pos[0]][s_pos[1]]
                animate_move(piece, s_pos, e_pos)
                backup_piece = starting_board[e_pos[0]][e_pos[1]]
                starting_board[e_pos[0]][e_pos[1]] = piece
                starting_board[s_pos[0]][s_pos[1]] = ""
                if promo:
                    mapping = {'q': 'queen', 'r': 'rook', 'b': 'bishop', 'n': 'knight'}
                    starting_board[e_pos[0]][e_pos[1]] = f"{piece[0]}_{mapping.get(promo, 'queen')}"
                if piece.endswith("king") and abs(e_pos[1] - s_pos[1]) == 2:
                    if e_pos[1] == 6:
                        starting_board[e_pos[0]][5] = starting_board[e_pos[0]][7]
                        starting_board[e_pos[0]][7] = ""
                    elif e_pos[1] == 2:
                        starting_board[e_pos[0]][3] = starting_board[e_pos[0]][0]
                        starting_board[e_pos[0]][0] = ""
                if piece.endswith("pawn") and (e_pos[0] == 0 or e_pos[0] == 7):
                    starting_board[e_pos[0]][e_pos[1]] = promote_pawn(piece)
                update_castle_rights(piece, s_pos)
                last_move = (s_pos, e_pos)
                turn = 'b' if turn == 'w' else 'w'
            if is_checkmate(starting_board, turn):
                winner = 'White' if ai_color == 'b' else 'Black'
                show_win_screen(winner)
                running = False
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if confirm_exit():
                    reset_game()
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if selected_piece:
                    if selected_piece[0] == turn and is_valid_move(starting_board, selected_piece, selected_pos, (mouse_row, mouse_col)):
                        old_row, old_col = selected_pos
                        animate_move(selected_piece, selected_pos, (mouse_row, mouse_col))
                        backup_piece = starting_board[mouse_row][mouse_col]
                        starting_board[mouse_row][mouse_col] = selected_piece
                        starting_board[old_row][old_col] = ""
                        if selected_piece.endswith("king") and abs(mouse_col - old_col) == 2:
                            if mouse_col == 6:
                                starting_board[mouse_row][5] = starting_board[mouse_row][7]
                                starting_board[mouse_row][7] = ""
                            elif mouse_col == 2:
                                starting_board[mouse_row][3] = starting_board[mouse_row][0]
                                starting_board[mouse_row][0] = ""
                        if selected_piece.endswith("pawn") and (mouse_row == 0 or mouse_row == 7):
                            starting_board[mouse_row][mouse_col] = promote_pawn(selected_piece)
                        if is_king_in_check(starting_board, turn):
                            starting_board[old_row][old_col] = selected_piece
                            starting_board[mouse_row][mouse_col] = backup_piece
                            if selected_piece.endswith("king") and abs(mouse_col - old_col) == 2:
                                if mouse_col == 6:
                                    starting_board[mouse_row][7] = starting_board[mouse_row][5]
                                    starting_board[mouse_row][5] = ""
                                elif mouse_col == 2:
                                    starting_board[mouse_row][0] = starting_board[mouse_row][3]
                                    starting_board[mouse_row][3] = ""
                        else:
                            update_castle_rights(selected_piece, selected_pos)
                            last_move = ((old_row, old_col), (mouse_row, mouse_col))
                            turn = 'b' if turn == 'w' else 'w'
                            if is_checkmate(starting_board, turn):
                                winner = 'White' if turn == 'b' else 'Black'
                                show_win_screen(winner)
                                running = False
                    selected_piece = None
                    selected_pos = None
                    legal_moves = []
                elif starting_board[mouse_row][mouse_col] and starting_board[mouse_row][mouse_col][0] == turn:
                    selected_piece = starting_board[mouse_row][mouse_col]
                    selected_pos = (mouse_row, mouse_col)
                    legal_moves = generate_legal_moves(starting_board, selected_piece, selected_pos)


            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0] and selected_piece:
                    dragging = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging and selected_piece:
                    new_row, new_col = mouse_y // square_size, mouse_x // square_size
                    if selected_piece[0] == turn and is_valid_move(starting_board, selected_piece, selected_pos, (new_row, new_col)):
                        old_row, old_col = selected_pos
                        animate_move(selected_piece, selected_pos, (new_row, new_col))
                        backup_piece = starting_board[new_row][new_col]
                        starting_board[new_row][new_col] = selected_piece
                        starting_board[old_row][old_col] = ""
                        if selected_piece.endswith("king") and abs(new_col - old_col) == 2:
                            if new_col == 6:
                                starting_board[new_row][5] = starting_board[new_row][7]
                                starting_board[new_row][7] = ""
                            elif new_col == 2:
                                starting_board[new_row][3] = starting_board[new_row][0]
                                starting_board[new_row][0] = ""
                        if selected_piece.endswith("pawn") and (new_row == 0 or new_row == 7):
                            starting_board[new_row][new_col] = promote_pawn(selected_piece)
                        if is_king_in_check(starting_board, turn):
                            starting_board[old_row][old_col] = selected_piece
                            starting_board[new_row][new_col] = backup_piece
                            if selected_piece.endswith("king") and abs(new_col - old_col) == 2:
                                if new_col == 6:
                                    starting_board[new_row][7] = starting_board[new_row][5]
                                    starting_board[new_row][5] = ""
                                elif new_col == 2:
                                    starting_board[new_row][0] = starting_board[new_row][3]
                                    starting_board[new_row][3] = ""
                        else:
                            update_castle_rights(selected_piece, selected_pos)
                            last_move = ((old_row, old_col), (new_row, new_col))
                            turn = 'b' if turn == 'w' else 'w'
                            if is_checkmate(starting_board, turn):
                                winner = 'White' if turn == 'b' else 'Black'
                                show_win_screen(winner)
                                running = False
                    selected_piece = None
                    selected_pos = None
                    dragging = False
                    legal_moves = []

        if dragging and selected_piece:
            drag_image = pygame.transform.smoothscale(pieces[selected_piece], (square_size, square_size))
            screen.blit(drag_image, (mouse_x - square_size // 2, mouse_y - square_size // 2))

        pygame.display.flip()


def main():
    while True:
        mode = show_home_screen()
        if mode in ('ai_easy', 'ai_medium', 'ai_hard'):
            level = mode.split('_')[1]
            game_loop(vs_ai=True, difficulty=level)
        elif mode == 'multi':
            game_loop(vs_ai=False)
        else:
            break
    pygame.quit()


if __name__ == "__main__":
    main()