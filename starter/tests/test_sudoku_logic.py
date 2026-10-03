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
    monkeypatch.setattr(sudoku_logic.random, "shuffle", lambda values: None)


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


def test_count_solutions_returns_one_for_a_completed_valid_board():
    board = make_solved_board()

    assert sudoku_logic.count_solutions(board) == 1


def test_count_solutions_returns_zero_for_a_contradictory_board():
    board = make_solved_board()
    board[0][0] = board[0][1]

    assert sudoku_logic.count_solutions(board) == 0


def test_count_solutions_stops_at_two_for_an_underconstrained_board():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.count_solutions(board) == 2


def test_remove_cells_leaves_the_requested_number_of_clues(monkeypatch):
    make_deterministic_random(monkeypatch)
    board = make_solved_board()

    sudoku_logic.remove_cells(board, clues=40)

    assert sum(value != sudoku_logic.EMPTY for row in board for value in row) == 40


def test_remove_cells_restores_a_clue_when_removal_is_non_unique(monkeypatch):
    make_deterministic_random(monkeypatch)
    board = make_solved_board()
    original_count_solutions = sudoku_logic.count_solutions
    rejected_removals = []

    def count_with_ambiguous_first_removal(candidate_board):
        if candidate_board[0][0] == sudoku_logic.EMPTY and not rejected_removals:
            rejected_removals.append((0, 0))
            return 2
        return original_count_solutions(candidate_board)

    monkeypatch.setattr(
        sudoku_logic, "count_solutions", count_with_ambiguous_first_removal
    )

    sudoku_logic.remove_cells(board, clues=80)

    assert rejected_removals == [(0, 0)]
    assert board[0][0] == make_solved_board()[0][0]
    assert sum(value != sudoku_logic.EMPTY for row in board for value in row) == 80


@pytest.mark.parametrize("clues", [16, 82, True, 35.5])
def test_remove_cells_rejects_invalid_clue_counts(clues):
    board = make_solved_board()

    with pytest.raises(ValueError):
        sudoku_logic.remove_cells(board, clues)

    assert board == make_solved_board()


@pytest.mark.parametrize("clues", [35, 47])
def test_generate_puzzle_returns_matching_puzzle_and_valid_solution(
    monkeypatch, clues
):
    make_deterministic_random(monkeypatch)

    puzzle, solution = sudoku_logic.generate_puzzle(clues)

    assert_valid_sudoku(solution)
    assert sum(value != sudoku_logic.EMPTY for row in puzzle for value in row) == clues
    assert sudoku_logic.count_solutions(puzzle) == 1
    for row in range(sudoku_logic.SIZE):
        for col in range(sudoku_logic.SIZE):
            if puzzle[row][col] != sudoku_logic.EMPTY:
                assert puzzle[row][col] == solution[row][col]


@pytest.mark.parametrize(
    ("difficulty", "expected_clues"),
    [("easy", 40), ("medium", 35), ("hard", 30)],
)
def test_generate_puzzle_is_unique_at_each_difficulty_target(
    difficulty, expected_clues
):
    clues = sudoku_logic.clues_for_difficulty(difficulty)

    assert clues == expected_clues
    puzzle, solution = sudoku_logic.generate_puzzle(clues)

    assert_valid_sudoku(solution)
    assert sum(value != sudoku_logic.EMPTY for row in puzzle for value in row) == clues
    assert sudoku_logic.count_solutions(puzzle) == 1


@pytest.mark.parametrize("difficulty", ["Easy", "expert", "", None])
def test_clues_for_difficulty_rejects_invalid_values(difficulty):
    with pytest.raises(ValueError, match="difficulty must be one of"):
        sudoku_logic.clues_for_difficulty(difficulty)