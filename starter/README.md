# Flask Sudoku

A Flask-based Sudoku game enhanced with unique-solution puzzle generation, difficulty levels, hints, validation, a timer, a Top 10 leaderboard, dark mode, and responsive styling.

## Features

- Standard 9x9 Sudoku gameplay
- Exactly one valid solution for every generated puzzle
- Three difficulty levels:
  - Easy
  - Medium
  - Hard
- Originally prefilled cells are locked
- Immediate feedback for invalid row, column, and 3x3 box entries
- Server-side puzzle checking
- Hint button that fills and locks one correct cell
- Hint counter
- Completion detection and message
- Game timer
- Top 10 leaderboard
- Leaderboard persistence using browser localStorage
- Leaderboard records include:
  - Player name
  - Completion time
  - Difficulty
  - Number of hints used
- Dark mode with persisted theme preference
- Alternating visual styling for 3x3 Sudoku boxes
- Responsive desktop and mobile layout
- Automated tests

## Technology

- Python
- Flask
- HTML
- CSS
- JavaScript
- pytest
- Node-backed frontend tests

## Project Structure

```text
starter/
├── app.py
├── sudoku_logic.py
├── requirements.txt
├── requirements-dev.txt
├── instruction.md
├── README.md
├── templates/
│   └── index.html
├── static/
│   ├── main.js
│   └── styles.css
├── tests/
│   ├── test_app.py
│   ├── test_sudoku_logic.py
│   └── test_frontend_gameplay.py
└── Screenshots/
