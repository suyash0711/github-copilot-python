import pytest

import sudoku_logic


def make_solved_board():
    return [
        [((row * 3 + row // 3 + col) % sudoku_logic.SIZE) + 1
         for col in range(sudoku_logic.SIZE)]
        for row in range(sudoku_logic.SIZE)
    ]


def assert_valid_sudoku(board):
    expected = set(range(1, sudoku_logic.SIZE + 1))
    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(set(row) == expected for row in board)
    assert all(
        {board[row][col] for row in range(sudoku_logic.SIZE)} == expected
        for col in range(sudoku_logic.SIZE)
    )
    for box_row in range(0, sudoku_logic.SIZE, 3):
        for box_col in range(0, sudoku_logic.SIZE, 3):
            box = {
                board[row][col]
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
            }
            assert box == expected


def make_deterministic_random(monkeypatch):
    calls = 0

    def next_coordinate(limit):
        nonlocal calls
        cell_index = calls // 2
        calls += 1
        return cell_index // sudoku_logic.SIZE if calls % 2 else cell_index % limit

    monkeypatch.setattr(sudoku_logic.random, "shuffle", lambda values: None)
    monkeypatch.setattr(sudoku_logic.random, "randrange", next_coordinate)


def test_create_empty_board_returns_nine_by_nine_zero_grid():
    board = sudoku_logic.create_empty_board()

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(value == sudoku_logic.EMPTY for row in board for value in row)


def test_deep_copy_is_independent_of_original_board():
    board = sudoku_logic.create_empty_board()

    copied_board = sudoku_logic.deep_copy(board)
    copied_board[0][0] = 7

    assert board[0][0] == sudoku_logic.EMPTY
    assert copied_board[0][0] == 7


def test_is_safe_accepts_a_candidate_with_no_conflicts():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.is_safe(board, 0, 0, 1)


@pytest.mark.parametrize(
    ("occupied_row", "occupied_col", "check_row", "check_col"),
    [
        (0, 4, 0, 8),  # Same row.
        (4, 0, 8, 0),  # Same column.
        (1, 1, 2, 2),  # Same 3x3 box.
    ],
)
def test_is_safe_rejects_row_column_and_box_conflicts(
    occupied_row, occupied_col, check_row, check_col
):
    board = sudoku_logic.create_empty_board()
    board[occupied_row][occupied_col] = 5

    assert not sudoku_logic.is_safe(board, check_row, check_col, 5)


def test_fill_board_completes_an_empty_board_with_valid_sudoku(monkeypatch):
    monkeypatch.setattr(sudoku_logic.random, "shuffle", lambda values: None)
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.fill_board(board)
    assert_valid_sudoku(board)


def test_remove_cells_leaves_the_requested_number_of_clues(monkeypatch):
    make_deterministic_random(monkeypatch)
    board = make_solved_board()

    sudoku_logic.remove_cells(board, clues=40)

    assert sum(value != sudoku_logic.EMPTY for row in board for value in row) == 40


@pytest.mark.parametrize("clues", [35, 47])
def test_generate_puzzle_returns_matching_puzzle_and_valid_solution(
    monkeypatch, clues
):
    make_deterministic_random(monkeypatch)

    puzzle, solution = sudoku_logic.generate_puzzle(clues)

    assert_valid_sudoku(solution)
    assert sum(value != sudoku_logic.EMPTY for row in puzzle for value in row) == clues
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            if puzzle[row][col] != sudoku_logic.EMPTY:
                assert puzzle[row][col] == solution[row][col]