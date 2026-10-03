from flask import Flask, render_template, jsonify, request
import sudoku_logic

app = Flask(__name__)

# Keep a simple in-memory store for current puzzle and solution
CURRENT = {
    'puzzle': None,
    'solution': None,
    'hints_used': 0,
    'hinted_cells': set(),
}


def get_submitted_board(data):
    board = data.get('board') if isinstance(data, dict) else None
    if (
        not isinstance(board, list)
        or len(board) != sudoku_logic.SIZE
        or any(not isinstance(row, list) or len(row) != sudoku_logic.SIZE for row in board)
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < sudoku_logic.EMPTY
            or value > sudoku_logic.SIZE
            for row in board
            for value in row
        )
    ):
        return None
    return board

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new')
def new_game():
    difficulty = request.args.get('difficulty')
    requested_clues = request.args.get('clues')

    if difficulty is not None:
        try:
            clues = sudoku_logic.clues_for_difficulty(difficulty)
        except ValueError as error:
            return jsonify({'error': str(error)}), 400

        if requested_clues is not None:
            try:
                legacy_clues = int(requested_clues)
            except ValueError:
                return jsonify({'error': 'clues must be an integer'}), 400
            if legacy_clues != clues:
                return jsonify({
                    'error': 'difficulty and clues parameters conflict'
                }), 400
    else:
        try:
            clues = int(requested_clues) if requested_clues is not None else 35
        except ValueError:
            return jsonify({'error': 'clues must be an integer'}), 400

    try:
        puzzle, solution = sudoku_logic.generate_puzzle(clues)
    except ValueError as error:
        return jsonify({'error': str(error)}), 503
    CURRENT['puzzle'] = puzzle
    CURRENT['solution'] = solution
    CURRENT['hints_used'] = 0
    CURRENT['hinted_cells'] = set()
    return jsonify({'puzzle': puzzle})

@app.route('/check', methods=['POST'])
def check_solution():
    board = get_submitted_board(request.get_json(silent=True))
    solution = CURRENT.get('solution')
    if solution is None:
        return jsonify({'error': 'No game in progress'}), 400
    if board is None:
        return jsonify({'error': 'Board must be a 9x9 grid of values from 0 to 9'}), 400

    incorrect = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if board[i][j] != solution[i][j]:
                incorrect.append([i, j])
    solved = not incorrect and all(
        value != sudoku_logic.EMPTY for row in board for value in row
    )
    return jsonify({'incorrect': incorrect, 'solved': solved})


@app.route('/hint', methods=['POST'])
def get_hint():
    puzzle = CURRENT.get('puzzle')
    solution = CURRENT.get('solution')
    if puzzle is None or solution is None:
        return jsonify({'error': 'No game in progress', 'hints_used': 0}), 400

    board = get_submitted_board(request.get_json(silent=True))
    if board is None:
        return jsonify({
            'error': 'Board must be a 9x9 grid of values from 0 to 9',
            'hints_used': CURRENT['hints_used'],
        }), 400

    eligible_cells = [
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if puzzle[row][col] == sudoku_logic.EMPTY
        and board[row][col] == sudoku_logic.EMPTY
        and (row, col) not in CURRENT['hinted_cells']
    ]
    if not eligible_cells:
        return jsonify({
            'error': 'No empty cells are available for a hint',
            'hints_used': CURRENT['hints_used'],
        }), 409

    row, col = eligible_cells[0]
    CURRENT['hinted_cells'].add((row, col))
    CURRENT['hints_used'] += 1
    return jsonify({
        'row': row,
        'col': col,
        'value': solution[row][col],
        'hints_used': CURRENT['hints_used'],
    })

if __name__ == '__main__':
    app.run(debug=True)