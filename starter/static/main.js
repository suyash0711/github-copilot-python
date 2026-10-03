// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const LEADERBOARD_KEY = 'flask-sudoku.leaderboard.v1';
const DIFFICULTIES = new Set(['easy', 'medium', 'hard']);
let puzzle = [];
let currentDifficulty = 'medium';
let hintsUsed = 0;
let timerStartedAt = null;
let elapsedTimeMs = 0;
let timerInterval = null;
let gameCompleted = false;

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      input.addEventListener('input', (e) => {
        const message = document.getElementById('message');
        if (e.target.disabled) {
          e.target.value = e.target.dataset.lockedValue || puzzle[i][j] || '';
          return;
        }
        const val = e.target.value.replace(/[^1-9]/g, '');
        e.target.value = val;
        const inputs = boardDiv.getElementsByTagName('input');
        for (const cell of inputs) {
          if (!cell.disabled) cell.classList.remove('incorrect');
        }
        message.innerText = '';
        updateConflictFeedback(inputs);
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  document.getElementById('hint-count').innerText = 'Hints used: 0';
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.dataset.lockedValue = val;
        inp.className += ' prefilled';
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }
}

function formatTime(timeMs) {
  const totalSeconds = Math.floor(timeMs / 1000);
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function updateTimerDisplay() {
  const elapsed = timerStartedAt === null
    ? elapsedTimeMs
    : performance.now() - timerStartedAt;
  document.getElementById('game-timer').textContent = `Time: ${formatTime(elapsed)}`;
}

function startTimer() {
  if (timerInterval !== null) clearInterval(timerInterval);
  elapsedTimeMs = 0;
  timerStartedAt = performance.now();
  timerInterval = setInterval(updateTimerDisplay, 1000);
  updateTimerDisplay();
}

function stopTimer() {
  if (timerStartedAt !== null) {
    elapsedTimeMs = Math.max(0, performance.now() - timerStartedAt);
  }
  if (timerInterval !== null) clearInterval(timerInterval);
  timerInterval = null;
  timerStartedAt = null;
  updateTimerDisplay();
  return elapsedTimeMs;
}

function isValidLeaderboardRecord(record) {
  return record !== null
    && typeof record === 'object'
    && typeof record.name === 'string'
    && record.name.trim().length > 0
    && typeof record.timeMs === 'number'
    && Number.isFinite(record.timeMs)
    && record.timeMs >= 0
    && DIFFICULTIES.has(record.difficulty)
    && Number.isInteger(record.hintsUsed)
    && record.hintsUsed >= 0;
}

function readLeaderboard() {
  try {
    const stored = localStorage.getItem(LEADERBOARD_KEY);
    if (stored === null) return [];
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isValidLeaderboardRecord).map(record => ({
      name: record.name.trim(),
      timeMs: record.timeMs,
      difficulty: record.difficulty,
      hintsUsed: record.hintsUsed
    })).sort((left, right) => left.timeMs - right.timeMs).slice(0, 10);
  } catch (_error) {
    return [];
  }
}

function renderLeaderboard(records = readLeaderboard()) {
  const body = document.getElementById('leaderboard-entries');
  body.replaceChildren();
  for (const record of records) {
    const row = document.createElement('tr');
    const values = [
      record.name,
      formatTime(record.timeMs),
      record.difficulty[0].toUpperCase() + record.difficulty.slice(1),
      String(record.hintsUsed)
    ];
    for (const value of values) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    }
    body.appendChild(row);
  }
}

function saveLeaderboard(records) {
  try {
    localStorage.setItem(LEADERBOARD_KEY, JSON.stringify(records));
    return true;
  } catch (_error) {
    return false;
  }
}

function recordCompletion(timeMs) {
  const name = prompt('Puzzle solved. Enter your name for the leaderboard:');
  if (name === null || !name.trim()) return;

  const records = readLeaderboard();
  records.push({
    name: name.trim(),
    timeMs,
    difficulty: currentDifficulty,
    hintsUsed
  });
  records.sort((left, right) => left.timeMs - right.timeMs);
  const topRecords = records.slice(0, 10);
  saveLeaderboard(topRecords);
  renderLeaderboard(topRecords);
}

function getBoardValues(inputs) {
  const board = [];
  for (let row = 0; row < SIZE; row++) {
    board[row] = [];
    for (let col = 0; col < SIZE; col++) {
      const value = inputs[row * SIZE + col].value;
      board[row][col] = value ? parseInt(value, 10) : 0;
    }
  }
  return board;
}

function findConflictingCells(board) {
  const conflicts = new Set();
  for (let row = 0; row < SIZE; row++) {
    for (let col = 0; col < SIZE; col++) {
      const value = board[row][col];
      if (!value) continue;

      for (let otherCol = col + 1; otherCol < SIZE; otherCol++) {
        if (board[row][otherCol] === value) {
          conflicts.add(row * SIZE + col);
          conflicts.add(row * SIZE + otherCol);
        }
      }
      for (let otherRow = row + 1; otherRow < SIZE; otherRow++) {
        if (board[otherRow][col] === value) {
          conflicts.add(row * SIZE + col);
          conflicts.add(otherRow * SIZE + col);
        }
      }

      const boxRow = Math.floor(row / 3) * 3;
      const boxCol = Math.floor(col / 3) * 3;
      for (let otherRow = boxRow; otherRow < boxRow + 3; otherRow++) {
        for (let otherCol = boxCol; otherCol < boxCol + 3; otherCol++) {
          if (
            (otherRow > row || (otherRow === row && otherCol > col)) &&
            board[otherRow][otherCol] === value
          ) {
            conflicts.add(row * SIZE + col);
            conflicts.add(otherRow * SIZE + otherCol);
          }
        }
      }
    }
  }
  return conflicts;
}

function updateConflictFeedback(inputs) {
  const conflicts = findConflictingCells(getBoardValues(inputs));
  for (let idx = 0; idx < inputs.length; idx++) {
    const input = inputs[idx];
    if (!input.disabled) input.classList.toggle('invalid', conflicts.has(idx));
  }
  if (conflicts.size) {
    const message = document.getElementById('message');
    message.style.color = '#d32f2f';
    message.innerText = 'Conflicting entries are highlighted.';
  }
}

async function newGame() {
  const difficulty = document.getElementById('difficulty').value;
  const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
  const data = await res.json();
  if (!res.ok) {
    document.getElementById('message').innerText = data.error || 'Could not start a new game.';
    return;
  }
  renderPuzzle(data.puzzle);
  currentDifficulty = difficulty;
  hintsUsed = 0;
  gameCompleted = false;
  document.getElementById('hint-count').innerText = 'Hints used: 0';
  document.getElementById('message').innerText = '';
  startTimer();
}

async function requestHint() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const res = await fetch('/hint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board: getBoardValues(inputs)})
  });
  const data = await res.json();
  const message = document.getElementById('message');
  if (Number.isInteger(data.hints_used) && data.hints_used >= 0) {
    hintsUsed = data.hints_used;
  }
  document.getElementById('hint-count').innerText = `Hints used: ${data.hints_used}`;
  if (!res.ok) {
    message.style.color = '#d32f2f';
    message.innerText = data.error || 'No hint is available.';
    return;
  }

  const idx = data.row * SIZE + data.col;
  const input = inputs[idx];
  input.value = data.value;
  input.disabled = true;
  input.dataset.lockedValue = data.value;
  input.classList.remove('invalid', 'incorrect');
  input.classList.add('hinted');
  message.innerText = '';
  updateConflictFeedback(inputs);
}

async function checkSolution() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = getBoardValues(inputs);
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board})
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (data.error) {
    msg.style.color = '#d32f2f';
    msg.innerText = data.error;
    return;
  }
  const incorrect = new Set(data.incorrect.map(x => x[0]*SIZE + x[1]));
  for (let idx = 0; idx < inputs.length; idx++) {
    const inp = inputs[idx];
    if (inp.disabled) continue;
    inp.classList.toggle('incorrect', incorrect.has(idx));
  }
  if (data.solved === true) {
    if (!gameCompleted) {
      gameCompleted = true;
      const completionTime = stopTimer();
      recordCompletion(completionTime);
    }
    msg.style.color = '#388e3c';
    msg.innerText = 'Congratulations! You solved it!';
  } else {
    msg.style.color = '#d32f2f';
    msg.innerText = 'The puzzle is incomplete or contains incorrect entries.';
  }
}

// Wire buttons
window.addEventListener('load', () => {
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  document.getElementById('get-hint').addEventListener('click', requestHint);
  renderLeaderboard();
  // initialize
  newGame();
});