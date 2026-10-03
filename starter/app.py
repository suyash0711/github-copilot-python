from flask import Flask, render_template, jsonify, request
import sudoku_logic

app = Flask(__name__)

# Keep a simple in-memory store for current puzzle and solution
CURRENT = {
    'puzzle': None,
    'solution': None
}

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
    return jsonify({'puzzle': puzzle})

@app.route('/check', methods=['POST'])
def check_solution():
    data = request.json
    board = data.get('board')
    solution = CURRENT.get('solution')
    if solution is None:
        return jsonify({'error': 'No game in progress'}), 400
    incorrect = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if board[i][j] != solution[i][j]:
                incorrect.append([i, j])
    return jsonify({'incorrect': incorrect})

if __name__ == '__main__':
    app.run(debug=True)