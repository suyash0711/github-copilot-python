import copy
import random

SIZE = 9
EMPTY = 0
MINIMUM_CLUES = 17
MAX_REMOVAL_ATTEMPTS = 10
DIFFICULTY_CLUES = {
    "easy": 40,
    "medium": 35,
    "hard": 30,
}


def clues_for_difficulty(difficulty):
    try:
        return DIFFICULTY_CLUES[difficulty]
    except (KeyError, TypeError):
        valid_difficulties = ", ".join(DIFFICULTY_CLUES)
        raise ValueError(
            f"difficulty must be one of: {valid_difficulties}"
        ) from None

def deep_copy(board):
    return copy.deepcopy(board)

def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]

def is_safe(board, row, col, num):
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True


def count_solutions(board):
    if (
        not isinstance(board, (list, tuple))
        or len(board) != SIZE
        or any(not isinstance(row, (list, tuple)) or len(row) != SIZE for row in board)
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < EMPTY
            or value > SIZE
            for row in board
            for value in row
        )
    ):
        return 0

    working_board = [list(row) for row in board]
    for row in range(SIZE):
        for col in range(SIZE):
            value = working_board[row][col]
            if value != EMPTY:
                working_board[row][col] = EMPTY
                is_valid = is_safe(working_board, row, col, value)
                working_board[row][col] = value
                if not is_valid:
                    return 0

    solution_count = 0

    def search():
        nonlocal solution_count
        if solution_count >= 2:
            return

        best_cell = None
        best_candidates = None
        for row in range(SIZE):
            for col in range(SIZE):
                if working_board[row][col] != EMPTY:
                    continue
                candidates = [
                    candidate
                    for candidate in range(1, SIZE + 1)
                    if is_safe(working_board, row, col, candidate)
                ]
                if not candidates:
                    return
                if best_candidates is None or len(candidates) < len(best_candidates):
                    best_cell = (row, col)
                    best_candidates = candidates

        if best_cell is None:
            solution_count += 1
            return

        row, col = best_cell
        for candidate in best_candidates:
            working_board[row][col] = candidate
            search()
            working_board[row][col] = EMPTY
            if solution_count >= 2:
                return

    search()
    return solution_count


def remove_cells(board, clues):
    if (
        not isinstance(clues, int)
        or isinstance(clues, bool)
        or clues < MINIMUM_CLUES
        or clues > SIZE * SIZE
    ):
        raise ValueError(f"clues must be between {MINIMUM_CLUES} and {SIZE * SIZE}")
    if any(board[row][col] == EMPTY for row in range(SIZE) for col in range(SIZE)):
        raise ValueError("remove_cells requires a complete solution board")
    if count_solutions(board) != 1:
        raise ValueError("remove_cells requires a valid solution board")

    original_board = deep_copy(board)
    for _ in range(MAX_REMOVAL_ATTEMPTS):
        board[:] = deep_copy(original_board)
        cells = [
            (row, col)
            for row in range(SIZE)
            for col in range(SIZE)
        ]
        random.shuffle(cells)
        remaining_clues = SIZE * SIZE

        for row, col in cells:
            if remaining_clues == clues:
                return

            clue = board[row][col]
            board[row][col] = EMPTY
            if count_solutions(board) == 1:
                remaining_clues -= 1
            else:
                board[row][col] = clue

        if remaining_clues == clues:
            return

    board[:] = original_board
    raise ValueError(f"could not generate a unique puzzle with exactly {clues} clues")

def generate_puzzle(clues=35):
    board = create_empty_board()
    if not fill_board(board):
        raise RuntimeError("could not generate a complete Sudoku solution")
    solution = deep_copy(board)
    remove_cells(board, clues)
    puzzle = deep_copy(board)
    return puzzle, solution
