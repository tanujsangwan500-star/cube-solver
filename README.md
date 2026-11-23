# Rubik's Cube AI Solver (IDA*)

A command-line solver for the 3x3x3 Rubik's Cube, written in pure Python. It finds a **shortest** solution (in Half-Turn Metric) using **IDA\* (Iterative Deepening A\*)** with an admissible heuristic, move pruning and a transposition table.

File: `AIWP_Rubix_Cube_Solver.py`

---

## Features

- 54-facelet cube representation, with all 18 move permutations **generated automatically** from 3D geometry (no hand-typed tables)
- IDA\* search that returns optimal solutions in HTM (U, U', U2 and the same for R, F, D, L, B)
- Admissible heuristic: `max(ceil(corners/4), ceil(edges/4), ceil(stickers/20))`
- Pruning: no same face twice in a row, canonical order for opposite faces, per-iteration transposition table
- Random scramble generator or manual scramble input
- Solution verification by replaying it on the cube
- Built-in self-tests for the cube engine
- Performance report: nodes explored, IDA\* iterations, execution time, solution length
- BFS, IDDFS and A\* included for comparison

## Requirements

- Python 3.6 or newer
- No external libraries (uses only `random`, `time`, `heapq`, `collections`)

## How to Run

```bash
python AIWP_Rubix_Cube_Solver.py
```

The program first runs the engine self-tests, then asks:

```
1. Generate random scramble
2. Enter your own scramble
```

- **Option 1** creates a random scramble of `SCRAMBLE_LENGTH` moves (default 5).
- **Option 2** asks for moves separated by spaces, for example: `R U R' U'`

### Move notation

| Move | Meaning |
|---|---|
| `R` | Right face, 90 degrees clockwise |
| `R'` | Right face, 90 degrees anticlockwise |
| `R2` | Right face, 180 degrees |

Faces: `U` (Up), `R` (Right), `F` (Front), `D` (Down), `L` (Left), `B` (Back). An invalid move stops the program with an error message.

### Sample output

```
Scramble:
R U R' U'
...
Starting IDA* search...

========== SOLUTION ==========
U R U' R'
Number of moves: 4

Solution Verification:
SUCCESS: Cube solved correctly.

========== PERFORMANCE REPORT ==========
Nodes explored: 27
IDA* iterations: 4
Execution time: 0.0023 seconds
Solution length: 4
========================================
```

## Configuration

Edit the constants at the top of the file:

| Constant | Default | Meaning |
|---|---|---|
| `SCRAMBLE_LENGTH` | 5 | Length of the random scramble |
| `MAX_SEARCH_DEPTH` | 20 | Largest IDA\* bound (20 is the maximum needed for any cube in HTM) |
| `MAX_NODES` | 1,000,000 | Search stops after this many nodes; increase it for longer scrambles |

## Using it from another Python file

```python
import AIWP_Rubix_Cube_Solver as cube

state = cube.apply_moves(cube.SOLVED_STATE, cube.parse_moves("R U F' D2"))
solution, stats = cube.ida_star(state, max_depth=20, max_nodes=1_000_000)

print(solution)                 # list of moves, or None if the limit was reached
print(stats.nodes, stats.iterations, stats.elapsed())
```

## Code Structure

| Section | Main functions |
|---|---|
| Facelet geometry | `facelet_position`, `FACELET_INFO`, `POSITION_LOOKUP` |
| Move generation | `rotate_vector`, `generate_quarter_turn`, `generate_move_tables` |
| Cube operations | `apply_move`, `apply_moves`, `parse_moves`, `validate_cube`, `is_solved`, `display_cube` |
| Scramble | `generate_scramble` |
| Heuristic | `heuristic` |
| Search | `ida_star` (main solver), `bfs`, `iddfs`, `astar` |
| Reporting and tests | `SearchStatistics`, `print_statistics`, `run_tests`, `main` |

## How It Works

1. Each sticker is stored with its 3D position and outward normal. A face turn rotates the stickers on that face by 90 degrees, which gives the move permutation.
2. IDA\* starts with the bound `h(start)` and runs a depth-first search that cuts any node with `depth + h > bound`. If no solution is found, the bound rises to the smallest cut-off value and the search repeats.
3. Because the heuristic never overestimates, the first solution found is optimal.

## Performance (measured)

| Scramble length | Example nodes explored | Time |
|---|---|---|
| 1-4 | 1 to 27 | under 0.01 s |
| 5 | 260 | 0.03 s |
| 6 | 3,836 | 0.35 s |
| 7 | 18,134 | 1.8 s |
| 8 | 214,562 | 20 s |
| 9 | over 1,000,000 (default limit reached) | about 93 s, not solved |

Times are from one machine and will vary. Cost per node is about 93 microseconds.

## Complexity

- **Time:** O(b^d), with effective branching factor b about 13.3 (18 moves, reduced by pruning) and solution depth d at most 20. One node costs O(1): 54 operations per move and about 100 per heuristic.
- **Space:** O(d) for the search path, plus O(N) for the transposition table (at most `MAX_NODES` entries).

## Limitations

- The heuristic is simple, so scrambles of about 9 or more moves exceed the default node limit. Raise `MAX_NODES` (slow in Python) or use stronger heuristics such as pattern databases.
- Only a scramble applied to a solved cube is accepted, not a cube entered sticker by sticker.
- `bfs`, `iddfs` and `astar` are for comparison and are not called from `main()`.
