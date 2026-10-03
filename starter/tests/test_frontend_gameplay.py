import json
import shutil
import subprocess
from pathlib import Path

import pytest


NODE = shutil.which("node")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(NODE is None, reason="Node.js is not installed")
def test_frontend_locks_prefills_and_updates_rule_conflict_feedback():
    script_path = json.dumps(str(PROJECT_ROOT / "static" / "main.js"))
    script = f"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function makeElement(tagName) {{
  const classes = new Set();
  let className = '';
  let inputValue = '';
  let textContent = '';
  const element = {{
    tagName,
    children: [],
    dataset: {{}},
    disabled: false,
    listeners: {{}},
    style: {{}},
    innerText: '',
    value: '',
    appendChild(child) {{ this.children.push(child); }},
    replaceChildren(...children) {{ this.children = children; }},
    addEventListener(name, handler) {{ this.listeners[name] = handler; }},
    getElementsByTagName(name) {{
      const matches = this.tagName === name ? [this] : [];
      return matches.concat(...this.children.map(child => child.getElementsByTagName(name)));
    }},
    classList: {{
      add(name) {{ classes.add(name); className = [...classes].join(' '); }},
      remove(name) {{ classes.delete(name); className = [...classes].join(' '); }},
      contains(name) {{ return classes.has(name); }},
      toggle(name, force) {{
        const shouldAdd = force === undefined ? !classes.has(name) : force;
        if (shouldAdd) classes.add(name);
        else classes.delete(name);
        className = [...classes].join(' ');
        return shouldAdd;
      }}
    }}
  }};
  Object.defineProperty(element, 'className', {{
    get() {{ return className; }},
    set(value) {{
      className = value;
      classes.clear();
      value.split(/\\s+/).filter(Boolean).forEach(name => classes.add(name));
    }}
  }});
  Object.defineProperty(element, 'value', {{
    get() {{ return inputValue; }},
    set(value) {{ inputValue = String(value); }}
  }});
  Object.defineProperty(element, 'textContent', {{
    get() {{ return textContent; }},
    set(value) {{ textContent = String(value); }}
  }});
  Object.defineProperty(element, 'innerHTML', {{
    set() {{ this.children = []; }}
  }});
  return element;
}}

const board = makeElement('div');
const message = makeElement('span');
const hintCount = makeElement('span');
const timerDisplay = makeElement('p');
const leaderboardBody = makeElement('tbody');
const difficulty = makeElement('select');
difficulty.value = 'medium';
const document = {{
  createElement: makeElement,
  getElementById(id) {{
    if (id === 'sudoku-board') return board;
    if (id === 'hint-count') return hintCount;
    if (id === 'game-timer') return timerDisplay;
    if (id === 'leaderboard-entries') return leaderboardBody;
    if (id === 'difficulty') return difficulty;
    return message;
  }}
}};
let clockNow = 0;
let nextIntervalId = 1;
const intervals = new Map();
const storage = new Map();
let storageFails = false;
let promptedName = null;
let promptCalls = 0;
const localStorage = {{
  getItem(key) {{ if (storageFails) throw new Error('storage unavailable'); return storage.get(key) ?? null; }},
  setItem(key, value) {{ if (storageFails) throw new Error('storage unavailable'); storage.set(key, value); }}
}};
const context = {{
  document,
  window: {{ addEventListener() {{}} }},
  performance: {{ now: () => clockNow }},
  setInterval(callback, delay) {{ const id = nextIntervalId++; intervals.set(id, {{ callback, delay }}); return id; }},
  clearInterval(id) {{ intervals.delete(id); }},
  localStorage,
  prompt() {{ promptCalls++; return promptedName; }}
}};
vm.createContext(context);
const source = fs.readFileSync({script_path}, 'utf8');
vm.runInContext(source + '\\nglobalThis.gameplay = {{ renderPuzzle, findConflictingCells, checkSolution, requestHint, newGame, readLeaderboard, renderLeaderboard, recordCompletion, leaderboardKey: LEADERBOARD_KEY, getState: () => ({{ timerStartedAt, elapsedTimeMs, timerInterval, gameCompleted, hintsUsed, currentDifficulty }}) }};', context);

const puzzle = Array.from({{ length: 9 }}, () => Array(9).fill(0));
puzzle[0][0] = 5;
context.gameplay.renderPuzzle(puzzle);
const inputs = board.getElementsByTagName('input');
assert.equal(inputs.length, 81);
assert.equal(inputs[0].disabled, true);
assert.ok(inputs[0].className.includes('prefilled'));
assert.equal(inputs[1].disabled, false);
assert.ok(!inputs[1].className.includes('prefilled'));

inputs[1].value = '5';
inputs[1].listeners.input({{ target: inputs[1] }});
assert.equal(inputs[1].classList.contains('invalid'), true);
assert.match(message.innerText, /conflicting entries/i);

inputs[1].value = '3';
inputs[1].listeners.input({{ target: inputs[1] }});
assert.equal(inputs[1].value, '3');
assert.equal(inputs[1].classList.contains('invalid'), false);
assert.equal(message.innerText, '');

inputs[0].value = '9';
inputs[0].listeners.input({{ target: inputs[0] }});
assert.equal(inputs[0].value, '5');

function emptyBoard() {{ return Array.from({{ length: 9 }}, () => Array(9).fill(0)); }}
let boardValues = emptyBoard();
boardValues[0][0] = boardValues[0][8] = 1;
assert.deepEqual([...context.gameplay.findConflictingCells(boardValues)].sort((a, b) => a - b), [0, 8]);
boardValues = emptyBoard();
boardValues[0][0] = boardValues[8][0] = 2;
assert.deepEqual([...context.gameplay.findConflictingCells(boardValues)].sort((a, b) => a - b), [0, 72]);
boardValues = emptyBoard();
boardValues[0][0] = boardValues[2][2] = 3;
assert.deepEqual([...context.gameplay.findConflictingCells(boardValues)].sort((a, b) => a - b), [0, 20]);

(async () => {{
  context.fetch = async () => ({{ json: async () => ({{ incorrect: [], solved: false }}) }});
  await context.gameplay.checkSolution();
  assert.match(message.innerText, /incomplete or contains incorrect/i);

  context.fetch = async () => ({{ json: async () => ({{ incorrect: [[0, 1]], solved: false }}) }});
  await context.gameplay.checkSolution();
  assert.equal(inputs[1].classList.contains('incorrect'), true);

  context.fetch = async () => ({{ json: async () => ({{ incorrect: [], solved: true }}) }});
  await context.gameplay.checkSolution();
  assert.match(message.innerText, /congratulations/i);

  let hintRequest;
  context.fetch = async (url, options) => {{
    hintRequest = {{ url, options }};
    return {{
      ok: true,
      json: async () => ({{ row: 1, col: 1, value: 4, hints_used: 1 }})
    }};
  }};
  await context.gameplay.requestHint();
  const hintedCell = inputs[10];
  assert.equal(hintRequest.url, '/hint');
  assert.equal(hintRequest.options.method, 'POST');
  assert.deepEqual(Object.keys(JSON.parse(hintRequest.options.body)), ['board']);
  assert.equal(hintedCell.value, '4');
  assert.equal(hintedCell.disabled, true);
  assert.equal(hintedCell.classList.contains('hinted'), true);
  assert.equal(hintedCell.classList.contains('prefilled'), false);
  assert.equal(hintCount.innerText, 'Hints used: 1');
  hintedCell.value = '8';
  hintedCell.listeners.input({{ target: hintedCell }});
  assert.equal(hintedCell.value, '4');

  context.fetch = async () => ({{ ok: false, json: async () => ({{ error: 'failed' }}) }});
  await context.gameplay.newGame();
  assert.equal(context.gameplay.getState().timerStartedAt, null);
  assert.equal(intervals.size, 0);

  clockNow = 1000;
  difficulty.value = 'easy';
  context.fetch = async () => ({{ ok: true, json: async () => ({{ puzzle }}) }});
  await context.gameplay.newGame();
  assert.equal(context.gameplay.getState().timerStartedAt, 1000);
  assert.equal(timerDisplay.textContent, 'Time: 00:00');
  assert.equal(intervals.size, 1);
  clockNow = 7000;
  [...intervals.values()][0].callback();
  assert.equal(timerDisplay.textContent, 'Time: 00:06');

  clockNow = 9000;
  difficulty.value = 'hard';
  await context.gameplay.newGame();
  assert.equal(context.gameplay.getState().timerStartedAt, 9000);
  assert.equal(context.gameplay.getState().elapsedTimeMs, 0);
  assert.equal(intervals.size, 1);

  const storageKey = context.gameplay.leaderboardKey;
  context.fetch = async () => ({{ json: async () => ({{ incorrect: [], solved: false }}) }});
  await context.gameplay.checkSolution();
  assert.equal(promptCalls, 1);
  assert.equal(storage.has(storageKey), false);
  context.fetch = async () => ({{ json: async () => ({{ incorrect: [[0, 1]], solved: false }}) }});
  await context.gameplay.checkSolution();
  assert.equal(storage.has(storageKey), false);

  context.fetch = async () => ({{
    ok: true,
    json: async () => ({{ row: 0, col: 1, value: 6, hints_used: 2 }})
  }});
  await context.gameplay.requestHint();
  assert.equal(context.gameplay.getState().hintsUsed, 2);
  clockNow = 12500;
  promptedName = '<img src=x onerror=alert(1)>';
  const leaderboardName = promptedName;
  context.fetch = async () => ({{ json: async () => ({{ incorrect: [], solved: true }}) }});
  await context.gameplay.checkSolution();
  const savedRecords = JSON.parse(storage.get(storageKey));
  assert.equal(savedRecords.length, 1);
  assert.deepEqual(Object.keys(savedRecords[0]).sort(), ['difficulty', 'hintsUsed', 'name', 'timeMs']);
  assert.deepEqual(savedRecords[0], {{
    name: promptedName,
    timeMs: 3500,
    difficulty: 'hard',
    hintsUsed: 2
  }});
  assert.equal(storage.size, 1);
  assert.equal(storage.get(storageKey).includes('solution'), false);
  assert.equal(storage.get(storageKey).includes('puzzle'), false);
  assert.equal(intervals.size, 0);
  assert.equal(timerDisplay.textContent, 'Time: 00:03');
  assert.equal(leaderboardBody.children[0].children[0].textContent, promptedName);
  assert.equal(promptCalls, 2);

  await context.gameplay.checkSolution();
  assert.equal(promptCalls, 2);
  assert.equal(JSON.parse(storage.get(storageKey)).length, 1);

  clockNow = 15000;
  context.fetch = async () => ({{ ok: true, json: async () => ({{ puzzle }}) }});
  await context.gameplay.newGame();
  promptedName = '   ';
  context.fetch = async () => ({{ json: async () => ({{ incorrect: [], solved: true }}) }});
  await context.gameplay.checkSolution();
  assert.equal(promptCalls, 3);
  assert.equal(JSON.parse(storage.get(storageKey)).length, 1);
  assert.equal(intervals.size, 0);
  await context.gameplay.checkSolution();
  assert.equal(promptCalls, 3);

  leaderboardBody.replaceChildren();
  context.gameplay.renderLeaderboard();
  assert.equal(leaderboardBody.children.length, 1);
  assert.equal(leaderboardBody.children[0].children[0].textContent, leaderboardName);

  const records = Array.from({{ length: 12 }}, (_, index) => ({{
    name: `Player ${{index}}`,
    timeMs: 12000 - index * 1000,
    difficulty: 'medium',
    hintsUsed: index
  }}));
  storage.set(storageKey, JSON.stringify(records));
  const topRecords = context.gameplay.readLeaderboard();
  assert.equal(topRecords.length, 10);
  assert.equal(topRecords[0].timeMs, 1000);
  assert.equal(topRecords[9].timeMs, 10000);
  context.gameplay.renderLeaderboard(topRecords);
  assert.equal(leaderboardBody.children.length, 10);
  promptedName = 'Fast finisher';
  context.gameplay.recordCompletion(500);
  const savedTopRecords = JSON.parse(storage.get(storageKey));
  assert.equal(savedTopRecords.length, 10);
  assert.equal(savedTopRecords[0].timeMs, 500);
  assert.equal(savedTopRecords[9].timeMs, 9000);

  storage.set(storageKey, '{{broken json');
  assert.deepEqual([...context.gameplay.readLeaderboard()], []);
  storage.set(storageKey, JSON.stringify({{ records }}));
  assert.deepEqual([...context.gameplay.readLeaderboard()], []);
  storage.set(storageKey, JSON.stringify([
    records[0],
    {{ name: 'Missing fields' }},
    {{ name: 'Bad difficulty', timeMs: 1, difficulty: 'expert', hintsUsed: 0 }},
    {{ name: 'Bad time', timeMs: -1, difficulty: 'easy', hintsUsed: 0 }},
    {{ name: 'Non-finite time', timeMs: 'Infinity', difficulty: 'easy', hintsUsed: 0 }},
    {{ name: 'Bad hints', timeMs: 10, difficulty: 'easy', hintsUsed: 1.5 }}
  ]));
  assert.equal(context.gameplay.readLeaderboard().length, 1);

  storageFails = true;
  assert.deepEqual([...context.gameplay.readLeaderboard()], []);
  context.gameplay.renderLeaderboard();
  clockNow = 20000;
  context.fetch = async () => ({{ ok: true, json: async () => ({{ puzzle }}) }});
  await context.gameplay.newGame();
  promptedName = 'Storage unavailable';
  context.fetch = async () => ({{ json: async () => ({{ incorrect: [], solved: true }}) }});
  await context.gameplay.checkSolution();
  assert.equal(context.gameplay.getState().gameCompleted, true);
  assert.equal(intervals.size, 0);
}})().catch(error => {{
  console.error(error);
  process.exitCode = 1;
}});
"""
    result = subprocess.run(
        [NODE, "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr