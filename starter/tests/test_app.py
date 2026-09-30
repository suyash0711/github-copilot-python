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
    app_module.CURRENT.update(puzzle=None, solution=None)
    with app_module.app.test_client() as test_client:
        yield test_client
    app_module.CURRENT.update(puzzle=None, solution=None)


def test_index_route_renders_existing_game_controls(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<h1>Sudoku Game</h1>" in response.data
    assert b'id="sudoku-board"' in response.data
    assert b'id="new-game"' in response.data
    assert b'id="check-solution"' in response.data


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
    assert app_module.CURRENT == {"puzzle": puzzle, "solution": solution}


def test_check_route_reports_error_when_no_game_is_active(client):
    response = client.post("/check", json={"board": make_solved_board()})

    assert response.status_code == 400
    assert response.get_json() == {"error": "No game in progress"}


def test_check_route_returns_no_incorrect_cells_for_matching_solution(client):
    solution = make_solved_board()
    app_module.CURRENT["solution"] = solution

    response = client.post("/check", json={"board": solution})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": []}


def test_check_route_reports_coordinates_that_differ_from_solution(client):
    solution = make_solved_board()
    board = [row.copy() for row in solution]
    board[0][0] = (solution[0][0] % sudoku_logic.SIZE) + 1
    board[8][8] = (solution[8][8] % sudoku_logic.SIZE) + 1
    app_module.CURRENT["solution"] = solution

    response = client.post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.get_json() == {"incorrect": [[0, 0], [8, 8]]}


@pytest.mark.parametrize("asset_path", ["/static/main.js", "/static/styles.css"])
def test_existing_static_assets_are_served(client, asset_path):
    response = client.get(asset_path)

    assert response.status_code == 200
    assert response.data