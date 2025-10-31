import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame


# Display configuration
TILE_SIZE = 72
BOARD_SIZE = 8
WINDOW_WIDTH = TILE_SIZE * BOARD_SIZE
WINDOW_HEIGHT = TILE_SIZE * BOARD_SIZE + 56  # space for status bar
FPS = 60

# Colors
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)
SELECT = (246, 246, 105)
MOVE = (187, 203, 43)
CHECK = (214, 72, 56)
TEXT = (30, 30, 30)
PANEL = (245, 245, 245)
GRID = (80, 80, 80)


# Pieces are encoded as: 'P','N','B','R','Q','K' for white; lowercase for black
START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w"


def parse_fen(fen: str) -> Tuple[list[list[str]], str]:
    parts = fen.split()
    board_rows = parts[0].split("/")
    to_move = parts[1] if len(parts) > 1 else "w"
    board: list[list[str]] = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for r, row in enumerate(board_rows):
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
            else:
                board[r][c] = ch
                c += 1
    return board, to_move


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def is_white(piece: str) -> bool:
    return piece.isupper()


def is_black(piece: str) -> bool:
    return piece.islower()


def side_of(piece: str) -> Optional[str]:
    if piece == ".":
        return None
    return "w" if is_white(piece) else "b"


def king_position(board: list[list[str]], side: str) -> Tuple[int, int]:
    target = "K" if side == "w" else "k"
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == target:
                return r, c
    return -1, -1


def is_square_attacked(board: list[list[str]], r: int, c: int, by_side: str) -> bool:
    # Pawn attacks
    if by_side == "w":
        for dr, dc in [(-1, -1), (-1, 1)]:
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == "P":
                return True
    else:
        for dr, dc in [(1, -1), (1, 1)]:
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == "p":
                return True

    # Knight attacks
    for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc):
            p = board[rr][cc]
            if (by_side == "w" and p == "N") or (by_side == "b" and p == "n"):
                return True

    # Sliding pieces: bishops/rooks/queens
    # Diagonals
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        rr, cc = r + dr, c + dc
        while in_bounds(rr, cc):
            p = board[rr][cc]
            if p != ".":
                if by_side == "w" and (p == "B" or p == "Q"):
                    return True
                if by_side == "b" and (p == "b" or p == "q"):
                    return True
                break
            rr += dr
            cc += dc
    # Orthogonals
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        rr, cc = r + dr, c + dc
        while in_bounds(rr, cc):
            p = board[rr][cc]
            if p != ".":
                if by_side == "w" and (p == "R" or p == "Q"):
                    return True
                if by_side == "b" and (p == "r" or p == "q"):
                    return True
                break
            rr += dr
            cc += dc

    # King attacks (adjacent)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc):
                p = board[rr][cc]
                if (by_side == "w" and p == "K") or (by_side == "b" and p == "k"):
                    return True
    return False


def clone_board(board: list[list[str]]) -> list[list[str]]:
    return [row[:] for row in board]


Move = Tuple[int, int, int, int]  # r1, c1, r2, c2


def generate_pseudo_legal_moves(board: list[list[str]], side: str) -> List[Move]:
    moves: list[Move] = []
    forward = -1 if side == "w" else 1
    pawn_row_start = 6 if side == "w" else 1
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board[r][c]
            if p == "." or side_of(p) != side:
                continue

            if p.upper() == "P":
                # single push
                r1, c1 = r + forward, c
                if in_bounds(r1, c1) and board[r1][c1] == ".":
                    moves.append((r, c, r1, c1))
                    # double push
                    r2 = r + 2 * forward
                    if r == pawn_row_start and board[r2][c1] == ".":
                        moves.append((r, c, r2, c1))
                # captures
                for dc in (-1, 1):
                    rr, cc = r + forward, c + dc
                    if in_bounds(rr, cc) and board[rr][cc] != "." and side_of(board[rr][cc]) != side:
                        moves.append((r, c, rr, cc))

            elif p.upper() == "N":
                for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                    rr, cc = r + dr, c + dc
                    if in_bounds(rr, cc) and side_of(board[rr][cc]) != side:
                        moves.append((r, c, rr, cc))

            elif p.upper() == "B" or p.upper() == "R" or p.upper() == "Q":
                dirs = []
                if p.upper() in ("B", "Q"):
                    dirs += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                if p.upper() in ("R", "Q"):
                    dirs += [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for dr, dc in dirs:
                    rr, cc = r + dr, c + dc
                    while in_bounds(rr, cc):
                        if board[rr][cc] == ".":
                            moves.append((r, c, rr, cc))
                        else:
                            if side_of(board[rr][cc]) != side:
                                moves.append((r, c, rr, cc))
                            break
                        rr += dr
                        cc += dc

            elif p.upper() == "K":
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        rr, cc = r + dr, c + dc
                        if in_bounds(rr, cc) and side_of(board[rr][cc]) != side:
                            moves.append((r, c, rr, cc))
                # Castling omitted for simplicity
    return moves


def make_move(board: list[list[str]], move: Move) -> list[list[str]]:
    r1, c1, r2, c2 = move
    newb = clone_board(board)
    piece = newb[r1][c1]
    newb[r1][c1] = "."
    # promotion: auto to queen
    if piece.upper() == "P" and (r2 == 0 or r2 == BOARD_SIZE - 1):
        piece = "Q" if is_white(piece) else "q"
    newb[r2][c2] = piece
    return newb


def in_check(board: list[list[str]], side: str) -> bool:
    kr, kc = king_position(board, side)
    if kr == -1:
        return True
    opponent = "b" if side == "w" else "w"
    return is_square_attacked(board, kr, kc, opponent)


def generate_legal_moves(board: list[list[str]], side: str) -> List[Move]:
    legal: list[Move] = []
    for mv in generate_pseudo_legal_moves(board, side):
        nb = make_move(board, mv)
        if not in_check(nb, side):
            legal.append(mv)
    return legal


# Rendering helpers
def render_text(surface, text, size, color, center=None, topleft=None):
    font = pygame.font.SysFont("segoe ui symbol", size)
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center is not None:
        rect.center = center
    if topleft is not None:
        rect.topleft = topleft
    surface.blit(surf, rect)


UNICODE_PIECES = {
    "K": "\u2654",
    "Q": "\u2655",
    "R": "\u2656",
    "B": "\u2657",
    "N": "\u2658",
    "P": "\u2659",
    "k": "\u265A",
    "q": "\u265B",
    "r": "\u265C",
    "b": "\u265D",
    "n": "\u265E",
    "p": "\u265F",
}


@dataclass
class UIState:
    selected: Optional[Tuple[int, int]] = None
    legal_moves_from_selected: List[Move] = None
    dragging: bool = False
    drag_offset: Tuple[int, int] = (0, 0)


def square_at_pixel(x: int, y: int) -> Optional[Tuple[int, int]]:
    if 0 <= x < TILE_SIZE * BOARD_SIZE and 0 <= y < TILE_SIZE * BOARD_SIZE:
        r = y // TILE_SIZE
        c = x // TILE_SIZE
        return r, c
    return None


def draw_board(surface, board: list[list[str]], ui: UIState, to_move: str):
    # Squares
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            color = LIGHT if (r + c) % 2 == 0 else DARK
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, color, rect)

    # Highlight selected
    if ui.selected is not None:
        sr, sc = ui.selected
        pygame.draw.rect(
            surface,
            SELECT,
            (sc * TILE_SIZE, sr * TILE_SIZE, TILE_SIZE, TILE_SIZE),
        )

    # Compute check highlight
    if in_check(board, to_move):
        kr, kc = king_position(board, to_move)
        pygame.draw.rect(surface, CHECK, (kc * TILE_SIZE, kr * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # Legal move hints
    if ui.legal_moves_from_selected:
        for r1, c1, r2, c2 in ui.legal_moves_from_selected:
            cx = c2 * TILE_SIZE + TILE_SIZE // 2
            cy = r2 * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.circle(surface, MOVE, (cx, cy), 10)

    # Pieces
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece == ".":
                continue
            # Skip drawing the selected piece if dragging
            if ui.dragging and ui.selected == (r, c):
                continue
            symbol = UNICODE_PIECES[piece]
            px = c * TILE_SIZE + TILE_SIZE // 2
            py = r * TILE_SIZE + TILE_SIZE // 2
            render_text(surface, symbol, int(TILE_SIZE * 0.9), TEXT, center=(px, py))

    # Drag piece on top
    if ui.dragging and ui.selected is not None:
        sr, sc = ui.selected
        piece = board[sr][sc]
        if piece != ".":
            symbol = UNICODE_PIECES[piece]
            mx, my = pygame.mouse.get_pos()
            render_text(
                surface,
                symbol,
                int(TILE_SIZE * 0.9),
                TEXT,
                center=(mx - ui.drag_offset[0], my - ui.drag_offset[1]),
            )

    # Bottom panel
    pygame.draw.rect(surface, PANEL, (0, TILE_SIZE * BOARD_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT - TILE_SIZE * BOARD_SIZE))
    turn_text = "White to move" if to_move == "w" else "Black to move"
    render_text(surface, turn_text, 24, TEXT, topleft=(12, TILE_SIZE * BOARD_SIZE + 12))


def main():
    pygame.init()
    pygame.display.set_caption("Chess - Pygame")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    board, to_move = parse_fen(START_FEN)
    ui = UIState(selected=None, legal_moves_from_selected=[])

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    board, to_move = parse_fen(START_FEN)
                    ui = UIState(selected=None, legal_moves_from_selected=[])

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = square_at_pixel(*event.pos)
                    if pos is not None:
                        r, c = pos
                        piece = board[r][c]
                        if piece != "." and side_of(piece) == to_move:
                            ui.selected = (r, c)
                            ui.dragging = True
                            mx, my = event.pos
                            ui.drag_offset = (mx - (c * TILE_SIZE + TILE_SIZE // 2), my - (r * TILE_SIZE + TILE_SIZE // 2))
                            # compute legal moves from selection
                            legal = []
                            for mv in generate_legal_moves(board, to_move):
                                if (mv[0], mv[1]) == (r, c):
                                    legal.append(mv)
                            ui.legal_moves_from_selected = legal
                        else:
                            # deselect if clicked empty or opponent
                            ui.selected = None
                            ui.legal_moves_from_selected = []
                elif event.button == 3:
                    ui.selected = None
                    ui.legal_moves_from_selected = []
                    ui.dragging = False

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and ui.selected is not None:
                    dest = square_at_pixel(*event.pos)
                    if dest is not None:
                        r1, c1 = ui.selected
                        r2, c2 = dest
                        chosen: Optional[Move] = None
                        for mv in ui.legal_moves_from_selected:
                            if (mv[2], mv[3]) == (r2, c2):
                                chosen = mv
                                break
                        if chosen is not None:
                            board = make_move(board, chosen)
                            to_move = "b" if to_move == "w" else "w"
                    ui.selected = None
                    ui.legal_moves_from_selected = []
                    ui.dragging = False

        # Detect simple game end (checkmate/stalemate) - minimal
        legal_any = generate_legal_moves(board, to_move)
        screen.fill((0, 0, 0))
        draw_board(screen, board, ui, to_move)
        if not legal_any:
            msg = "Checkmate" if in_check(board, to_move) else "Stalemate"
            render_text(screen, msg + " - Press R to restart", 24, (20, 20, 20), topleft=(220, TILE_SIZE * BOARD_SIZE + 12))
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()








