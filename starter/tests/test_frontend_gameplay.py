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
  const element = {{
    tagName,
    children: [],
    dataset: {{}},
    disabled: false,
    listeners: {{}},
    style: {{}},
    innerText: '',
    appendChild(child) {{ this.children.push(child); }},
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
  Object.defineProperty(element, 'innerHTML', {{
    set() {{ this.children = []; }}
  }});
  return element;
}}

const board = makeElement('div');
const message = makeElement('span');
const document = {{
  createElement: makeElement,
  getElementById(id) {{ return id === 'sudoku-board' ? board : message; }}
}};
const context = {{ document, window: {{ addEventListener() {{}} }} }};
vm.createContext(context);
const source = fs.readFileSync({script_path}, 'utf8');
vm.runInContext(source + '\\nglobalThis.gameplay = {{ renderPuzzle, findConflictingCells, checkSolution }};', context);

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