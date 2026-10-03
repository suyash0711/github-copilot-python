import pytest

import app as app_module
import sudoku_logic


def make_solved_board():
    return [
        [((row * 3 + row // 3 + col) % sudoku_logic.SIZE) + 1
         for col in range(sudoku_logic.SIZE)]
        for row in range(sudoku_logic.SIZE)
    ]


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    app_module.CURRENT.update(
        puzzle=None, solution=None, hints_used=0, hinted_cells=set()
    )
    with app_module.app.test_client() as test_client:
        yield test_client
    app_module.CURRENT.update(
        puzzle=None, solution=None, hints_used=0, hinted_cells=set()
    )


def test_index_route_renders_existing_game_controls(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<h1>Sudoku Game</h1>" in response.data
    assert b'<select id="difficulty" name="difficulty">' in response.data
    assert b'<option value="medium" selected>Medium</option>' in response.data
    assert b'id="sudoku-board"' in response.data
    assert b'id="new-game"' in response.data
    assert b'id="check-solution"' in response.data
    assert b'id="get-hint"' in response.data
    assert b'id="hint-count"' in response.data


@pytest.mark.parametrize(
    ("query_string", "expected_clues"),
    [(None, 35), ({"clues": 42}, 42)],
)
def test_new_route_returns_generated_puzzle_and_stores_game(
    client, monkeypatch, query_string, expected_clues
):
    puzzle = [[0 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    solution = make_solved_board()
    received_clues = []

    def fake_generate_puzzle(clues):
        received_clues.append(clues)
        return puzzle, solution

    monkeypatch.setattr(
        app_module.sudoku_logic, "generate_puzzle", fake_generate_puzzle
    )

    response = client.get("/new", query_string=query_string)

    assert response.status_code == 200
    assert response.get_json() == {"puzzle": puzzle}
    assert received_clues == [expected_clues]
    assert app_module.CURRENT == {
        "puzzle": puzzle,
        "solution": solution,
        "hints_used": 0,
        "hinted_cells": set(),
    }


@pytest.mark.parametrize(
    ("difficulty", "expected_clues"),
    [("easy", 40), ("medium", 35), ("hard", 30)],
)
def test_new_route_maps_difficulty_to_clues(
    client, monkeypatch, difficulty, expected_clues
):
    puzzle = [[0 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    solution = make_solved_board()
    received_clues = []

    def fake_generate_puzzle(clues):
        received_clues.append(clues)
        return puzzle, solution

    monkeypatch.setattr(
        app_module.sudoku_logic, "generate_puzzle", fake_generate_puzzle
    )

    response = client.get("/new", query_string={"difficulty": difficulty})

    assert response.status_code == 200
    assert response.get_json() == {"puzzle": puzzle}
    assert received_clues == [expected_clues]


@pytest.mark.parametrize("difficulty", ["Easy", "expert", "", "MEDIUM"])
def test_new_route_rejects_invalid_difficulty(client, difficulty):
    response = client.get("/new", query_string={"difficulty": difficulty})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "difficulty must be one of: easy, medium, hard"
    }


def test_new_route_rejects_conflicting_difficulty_and_clues(client):
    response = client.get(
        "/new", query_string={"difficulty": "easy", "clues": 35}
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "difficulty and clues parameters conflict"
    }


def test_new_route_handles_bounded_generation_failure(client, monkeypatch):
    def fail_generation(clues):
        raise ValueError(f"could not generate a unique puzzle with exactly {clues} clues")

    monkeypatch.setattr(
        app_module.sudoku_logic, "generate_puzzle", fail_generation
    )

    response = client.get("/new?difficulty=hard")

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "could not generate a unique puzzle with exactly 30 clues"
    }


def test_check_route_reports_error_when_no_game_is_active(client):
    response = client.post("/check", json={"board": make_solved_board()})

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_check_route_returns_no_incorrect_cells_for_matching_solution(client):
    solution = make_solved_board()
    app_module.CURRENT["solution"] = solution

    response = client.post("/check", json={"board": solution})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [], "solved": True}


def test_check_route_does_not_mark_an_incomplete_board_as_solved(client):
    solution = make_solved_board()
    board = [row.copy() for row in solution]
    board[0][0] = sudoku_logic.EMPTY
    app_module.CURRENT["solution"] = solution

    response = client.post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [[0, 0]], "solved": False}


def test_check_route_reports_coordinates_that_differ_from_solution(client):
    solution = make_solved_board()
    board = [row.copy() for row in solution]
    board[0][0] = (solution[0][0] % sudoku_logic.SIZE) + 1
    board[8][8] = (solution[8][8] % sudoku_logic.SIZE) + 1
    app_module.CURRENT["solution"] = solution

    response = client.post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {
        "incorrect": [[0, 0], [8, 8]],
        "solved": False,
    }


def test_check_route_accepts_correctly_hinted_values(client):
    solution = make_solved_board()
    puzzle = [row.copy() for row in solution]
    puzzle[0][0] = sudoku_logic.EMPTY
    app_module.CURRENT.update(puzzle=puzzle, solution=solution)
    board = [row.copy() for row in puzzle]

    hint_response = client.post("/hint", json={"board": board})
    hint = hint_response.get_json()
    board[hint["row"]][hint["col"]] = hint["value"]
    check_response = client.post("/check", json={"board": board})

    assert hint_response.status_code == 200
    assert check_response.get_json() == {"incorrect": [], "solved": True}


def test_hint_returns_one_originally_empty_solution_value_without_solution_grid(client):
    solution = make_solved_board()
    puzzle = [row.copy() for row in solution]
    puzzle[0][0] = sudoku_logic.EMPTY
    puzzle[0][1] = sudoku_logic.EMPTY
    board = [row.copy() for row in puzzle]
    board[1][1] = sudoku_logic.EMPTY
    app_module.CURRENT.update(puzzle=puzzle, solution=solution)

    response = client.post("/hint", json={"board": board})
    data = response.get_json()

    assert response.status_code == 200
    assert set(data) == {"row", "col", "value", "hints_used"}
    assert puzzle[data["row"]][data["col"]] == sudoku_logic.EMPTY
    assert board[data["row"]][data["col"]] == sudoku_logic.EMPTY
    assert (data["row"], data["col"]) != (1, 1)
    assert data["value"] == solution[data["row"]][data["col"]]
    assert data["hints_used"] == 1
    assert "solution" not in data
    assert solution not in data.values()


def test_successive_hints_target_different_cells_and_increment_count(client):
    solution = make_solved_board()
    puzzle = [row.copy() for row in solution]
    puzzle[0][0] = sudoku_logic.EMPTY
    puzzle[0][1] = sudoku_logic.EMPTY
    board = [row.copy() for row in puzzle]
    app_module.CURRENT.update(puzzle=puzzle, solution=solution)

    first_response = client.post("/hint", json={"board": board})
    first_hint = first_response.get_json()
    board[first_hint["row"]][first_hint["col"]] = first_hint["value"]
    second_response = client.post("/hint", json={"board": board})
    second_hint = second_response.get_json()

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert (first_hint["row"], first_hint["col"]) != (
        second_hint["row"], second_hint["col"]
    )
    assert first_hint["hints_used"] == 1
    assert second_hint["hints_used"] == 2
    assert app_module.CURRENT["hints_used"] == 2


@pytest.mark.parametrize(
    "board",
    [None, {}, [[0]], [[0 for _ in range(9)] for _ in range(8)]],
)
def test_hint_rejects_invalid_or_missing_board_without_incrementing_count(
    client, board
):
    solution = make_solved_board()
    puzzle = [row.copy() for row in solution]
    puzzle[0][0] = sudoku_logic.EMPTY
    app_module.CURRENT.update(puzzle=puzzle, solution=solution)

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 400
    assert response.get_json()["hints_used"] == 0
    assert app_module.CURRENT["hints_used"] == 0


def test_hint_rejects_values_outside_zero_to_nine(client):
    solution = make_solved_board()
    puzzle = [row.copy() for row in solution]
    puzzle[0][0] = sudoku_logic.EMPTY
    board = [row.copy() for row in puzzle]
    board[0][0] = 10
    app_module.CURRENT.update(puzzle=puzzle, solution=solution)

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 400
    assert response.get_json()["hints_used"] == 0


def test_hint_returns_conflict_when_board_is_complete_without_incrementing(client):
    solution = make_solved_board()
    puzzle = [row.copy() for row in solution]
    puzzle[0][0] = sudoku_logic.EMPTY
    app_module.CURRENT.update(puzzle=puzzle, solution=solution)

    response = client.post("/hint", json={"board": solution})

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "No empty cells are available for a hint",
        "hints_used": 0,
    }
    assert app_module.CURRENT["hints_used"] == 0


def test_new_game_resets_hint_count_and_tracked_coordinates(client, monkeypatch):
    puzzle = [[0 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
    solution = make_solved_board()
    app_module.CURRENT.update(hints_used=3, hinted_cells={(0, 0), (0, 1)})
    monkeypatch.setattr(
        app_module.sudoku_logic,
        "generate_puzzle",
        lambda clues: (puzzle, solution),
    )

    response = client.get("/new")

    assert response.status_code == 200
    assert app_module.CURRENT["hints_used"] == 0
    assert app_module.CURRENT["hinted_cells"] == set()


def test_hint_requires_an_active_game(client):
    response = client.post("/hint", json={"board": make_solved_board()})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "No game in progress",
        "hints_used": 0,
    }


@pytest.mark.parametrize("asset_path", ["/static/main.js", "/static/styles.css"])
def test_existing_static_assets_are_served(client, asset_path):
    response = client.get(asset_path)

    assert response.status_code == 200
    assert response.data


def test_new_game_frontend_requests_selected_difficulty(client):
    response = client.get("/static/main.js")

    assert response.status_code == 200
    assert b"document.getElementById('difficulty').value" in response.data
    assert b"/new?difficulty=${encodeURIComponent(difficulty)}" in response.data