# GitHub Copilot Project Instructions

## Project

This project is a Flask-based Sudoku game being refactored from legacy Python code into a modular, maintainable application.

The goal is to preserve the existing functionality while adding difficulty levels, unique-solution puzzle generation, validation, hints, a timer, a Top 10 leaderboard, dark mode, responsive styling, and automated tests.

## General Coding Standards

- Use clear, readable and maintainable Python.
- Follow PEP 8 conventions.
- Use descriptive variable and function names.
- Keep functions focused on a single responsibility.
- Avoid unnecessary duplication.
- Prefer modular and reusable components.
- Add comments only where they improve understanding.
- Use type hints where practical.
- Handle errors gracefully.
- Do not introduce unnecessary dependencies.
- Preserve existing functionality when refactoring.
- Do not make unrelated changes to working code.

## Flask Structure

Keep Flask routing separate from Sudoku game logic wherever practical.

The application should use a clear separation between:

- Flask routes
- Sudoku generation
- Sudoku solving and validation
- Game state
- Frontend JavaScript
- CSS styling
- Tests

## Sudoku Requirements

The application must:

- Use a standard 9x9 Sudoku board.
- Follow standard Sudoku rules.
- Generate puzzles with exactly one valid solution.
- Support Easy, Medium and Hard difficulty levels.
- Lock originally prefilled cells.
- Allow users to enter values into editable cells.
- Detect invalid entries.
- Detect completed valid puzzles.
- Provide a hint that fills one correct cell.
- Lock cells inserted by the hint feature.

## Difficulty

Difficulty should change the number of cells initially revealed.

Use sensible values and keep them configurable rather than scattering magic numbers throughout the code.

## Frontend

The interface should:

- Work on desktop and mobile.
- Support light and dark modes.
- Maintain readable text and controls in both modes.
- Use alternating visual styling for the 3x3 Sudoku boxes.
- Avoid layout shifts when cells change state.
- Provide clear visual feedback for invalid entries and hints.
- Use accessible labels and controls where practical.

## Game Features

Implement:

- Difficulty selection
- Timer
- Check button
- Hint button
- Completion message
- Top 10 leaderboard
- Player name
- Completion time
- Difficulty
- Number of hints used
- Browser localStorage persistence
- Dark mode

The leaderboard must retain data after page refreshes and browser sessions.

## Testing

Tests must be written using a standard Python testing framework.

Tests should cover:

- Flask application behavior
- Sudoku generation
- Sudoku solving
- Unique solution validation
- Difficulty behavior
- Input validation
- Game completion
- Important feature behavior

Run the test suite after significant changes.

## Git and Copilot Workflow

Before implementing a significant feature:

1. Understand the existing implementation.
2. Ask Copilot to explain unfamiliar code when necessary.
3. Make the smallest sensible change.
4. Review Copilot's generated code.
5. Run the tests.
6. Fix failures before moving to the next feature.

Do not blindly accept Copilot suggestions. Evaluate generated code for correctness, security, maintainability and compatibility with the existing application.

## Dependencies

Prefer the Python standard library and existing project dependencies where possible.

Only introduce a new dependency when there is a clear reason for doing so.

## Important Constraint

Do not rewrite the entire project unnecessarily.

Refactor incrementally and preserve working behavior while introducing the new functionality.