
import random
import time
import heapq
from collections import defaultdict


# ============================================================
#  RUBIK'S CUBE AI SOLVER
#  Algorithm: IDA* (Iterative Deepening A*)
#  Metric: HTM (Half-Turn Metric)
#  Representation: 54 Facelets
# ============================================================


# -------------------- CONFIGURATION -------------------------

SCRAMBLE_LENGTH = 5
MAX_SEARCH_DEPTH = 20
MAX_NODES = 1_000_000

FACES = ["U", "R", "F", "D", "L", "B"]

FACE_NAMES = {
    "U": "Up",
    "R": "Right",
    "F": "Front",
    "D": "Down",
    "L": "Left",
    "B": "Back"
}

OPPOSITE = {
    "U": "D", "D": "U",
    "R": "L", "L": "R",
    "F": "B", "B": "F"
}

FACE_ORDER = {
    "U": 0, "D": 1,
    "R": 2, "L": 3,
    "F": 4, "B": 5
}

MOVE_NAMES = [
    face + suffix
    for face in FACES
    for suffix in ["", "'", "2"]
]

SOLVED_STRING = (
    "U" * 9 +
    "R" * 9 +
    "F" * 9 +
    "D" * 9 +
    "L" * 9 +
    "B" * 9
)

SOLVED_STATE = tuple(SOLVED_STRING)


# -------------------- FACELET GEOMETRY ----------------------

# Coordinates use:
# X = Right
# Y = Up
# Z = Front

FACE_NORMALS = {
    "U": (0, 1, 0),
    "R": (1, 0, 0),
    "F": (0, 0, 1),
    "D": (0, -1, 0),
    "L": (-1, 0, 0),
    "B": (0, 0, -1)
}


def facelet_position(face, row, col):

    if face == "U":
        return (col - 1, 1, row - 1)

    if face == "R":
        return (1, 1 - row, 1 - col)

    if face == "F":
        return (col - 1, 1 - row, 1)

    if face == "D":
        return (col - 1, -1, 1 - row)

    if face == "L":
        return (-1, 1 - row, col - 1)

    if face == "B":
        return (1 - col, 1 - row, -1)


# Store every sticker's position and normal.

FACELET_INFO = []
POSITION_LOOKUP = {}

for face in FACES:

    normal = FACE_NORMALS[face]

    for row in range(3):
        for col in range(3):

            position = facelet_position(face, row, col)

            index = len(FACELET_INFO)

            FACELET_INFO.append((position, normal))

            POSITION_LOOKUP[(position, normal)] = index


assert len(FACELET_INFO) == 54
assert len(POSITION_LOOKUP) == 54


# -------------------- VECTOR ROTATION -----------------------

def rotate_vector(vector, axis):

    # Rotate vector clockwise by 90 degrees
    # around the outward face normal.

    dot = sum(a * b for a, b in zip(axis, vector))

    cross = (
        axis[1] * vector[2] - axis[2] * vector[1],
        axis[2] * vector[0] - axis[0] * vector[2],
        axis[0] * vector[1] - axis[1] * vector[0]
    )

    return tuple(
        axis[i] * dot - cross[i]
        for i in range(3)
    )


# -------------------- GENERATE MOVE TABLES ------------------

def generate_quarter_turn(face):

    axis = FACE_NORMALS[face]

    permutation = [None] * 54

    for old_index, (position, normal) in enumerate(FACELET_INFO):

        if sum(
            position[i] * axis[i]
            for i in range(3)
        ) == 1:

            new_position = rotate_vector(position, axis)
            new_normal = rotate_vector(normal, axis)

        else:

            new_position = position
            new_normal = normal

        new_index = POSITION_LOOKUP[
            (new_position, new_normal)
        ]

        permutation[old_index] = new_index

    return permutation


def generate_move_tables():

    move_tables = {}

    for face in FACES:

        quarter = generate_quarter_turn(face)

        for suffix, turns in [
            ("", 1),
            ("'", 3),
            ("2", 2)
        ]:

            permutation = list(range(54))

            for _ in range(turns):

                permutation = [
                    quarter[permutation[i]]
                    for i in range(54)
                ]

            move_tables[face + suffix] = tuple(permutation)

    return move_tables


MOVE_TABLES = generate_move_tables()


# -------------------- CUBE OPERATIONS -----------------------

def apply_move(state, move):

    permutation = MOVE_TABLES[move]

    result = [None] * 54

    for old_index, new_index in enumerate(permutation):

        result[new_index] = state[old_index]

    return tuple(result)


def apply_moves(state, moves):

    for move in moves:

        state = apply_move(state, move)

    return state


def parse_moves(text):

    moves = text.strip().split()

    for move in moves:

        if move not in MOVE_TABLES:

            raise ValueError(
                "Invalid move: " + move
            )

    return moves


# -------------------- CUBE VALIDATION -----------------------

def validate_cube(state):

    if len(state) != 54:
        return False

    for face in FACES:

        if state.count(face) != 9:
            return False

    centers = [4, 13, 22, 31, 40, 49]

    expected = ["U", "R", "F", "D", "L", "B"]

    for index, colour in zip(centers, expected):

        if state[index] != colour:
            return False

    return True


def is_solved(state):

    return state == SOLVED_STATE


# -------------------- DISPLAY CUBE --------------------------

def display_cube(state):

    print("\n---------------- CUBE STATE ----------------")

    for face_index, face in enumerate(FACES):

        print("\n" + FACE_NAMES[face] + " Face:")

        start = face_index * 9

        stickers = state[start:start + 9]

        for row in range(3):

            print(
                " ".join(
                    stickers[row * 3:row * 3 + 3]
                )
            )

    print("--------------------------------------------")


# -------------------- RANDOM SCRAMBLE -----------------------

def generate_scramble(length):

    scramble = []

    previous_face = None

    for _ in range(length):

        possible_faces = [
            face for face in FACES
            if face != previous_face
        ]

        face = random.choice(possible_faces)

        suffix = random.choice(["", "'", "2"])

        scramble.append(face + suffix)

        previous_face = face

    return scramble


# -------------------- HEURISTIC -----------------------------

# Identify corner and edge cubies from their
# 3D coordinates.

cubie_positions = defaultdict(list)

for index, (position, normal) in enumerate(FACELET_INFO):

    cubie_positions[position].append(index)


CORNER_GROUPS = []
EDGE_GROUPS = []

for position, indices in cubie_positions.items():

    nonzero = sum(x != 0 for x in position)

    if nonzero == 3:
        CORNER_GROUPS.append(indices)

    elif nonzero == 2:
        EDGE_GROUPS.append(indices)


def heuristic(state):

    if state == SOLVED_STATE:
        return 0

    misplaced_corners = 0
    misplaced_edges = 0
    misplaced_stickers = 0

    # Count incorrect stickers.

    for i in range(54):

        if state[i] != SOLVED_STATE[i]:

            misplaced_stickers += 1

    # Count misplaced corner cubies.

    for group in CORNER_GROUPS:

        if any(
            state[i] != SOLVED_STATE[i]
            for i in group
        ):

            misplaced_corners += 1

    # Count misplaced edge cubies.

    for group in EDGE_GROUPS:

        if any(
            state[i] != SOLVED_STATE[i]
            for i in group
        ):

            misplaced_edges += 1

    # Admissible lower bounds.

    corner_bound = (misplaced_corners + 3) // 4

    edge_bound = (misplaced_edges + 3) // 4

    sticker_bound = (misplaced_stickers + 19) // 20

    return max(
        corner_bound,
        edge_bound,
        sticker_bound
    )


# -------------------- SEARCH STATISTICS ---------------------

class SearchStatistics:

    def __init__(self):

        self.nodes = 0
        self.iterations = 0
        self.start_time = 0
        self.end_time = 0

    def elapsed(self):

        if self.end_time == 0:
            return 0

        return self.end_time - self.start_time


class SearchLimitReached(Exception):
    pass


# -------------------- IDA* ALGORITHM -----------------------

def ida_star(
    start_state,
    max_depth=MAX_SEARCH_DEPTH,
    max_nodes=MAX_NODES
):

    statistics = SearchStatistics()

    statistics.start_time = time.perf_counter()

    initial_bound = heuristic(start_state)

    path = []

    bound = initial_bound

    # IDA* repeatedly increases the f-cost threshold.

    while bound <= max_depth:

        statistics.iterations += 1

        next_bound = float("inf")

        # Transposition table for the current iteration.
        # Last face is included because move pruning
        # depends on the previous face.

        visited = {}

        def search(state, depth, last_face):

            nonlocal next_bound

            if statistics.nodes >= max_nodes:

                raise SearchLimitReached

            h = heuristic(state)

            f = depth + h

            if f > bound:

                next_bound = min(next_bound, f)

                return False

            if is_solved(state):

                return True

            statistics.nodes += 1

            key = (state, last_face)

            previous_depth = visited.get(key)

            if (
                previous_depth is not None
                and previous_depth <= depth
            ):

                return False

            visited[key] = depth

            for move in MOVE_NAMES:

                face = move[0]

                # Do not repeat the same face consecutively.

                if face == last_face:
                    continue

                # Opposite faces commute.
                # Keep one canonical ordering.

                if last_face is not None:

                    if OPPOSITE[last_face] == face:

                        if (
                            FACE_ORDER[last_face]
                            > FACE_ORDER[face]
                        ):

                            continue

                new_state = apply_move(state, move)

                path.append(move)

                if search(
                    new_state,
                    depth + 1,
                    face
                ):

                    return True

                path.pop()

            return False

        try:

            if search(start_state, 0, None):

                statistics.end_time = time.perf_counter()

                return path.copy(), statistics

        except SearchLimitReached:

            statistics.end_time = time.perf_counter()

            return None, statistics

        if next_bound == float("inf"):

            break

        bound = next_bound

    statistics.end_time = time.perf_counter()

    return None, statistics


# -------------------- BFS ALGORITHM ------------------------

# Useful for demonstrating search algorithms on
# very shallow scrambles only.

def bfs(start_state, max_nodes=100000):

    from collections import deque

    queue = deque([(start_state, [])])

    visited = {start_state}

    nodes = 0

    while queue:

        state, path = queue.popleft()

        nodes += 1

        if state == SOLVED_STATE:

            return path, nodes

        if nodes >= max_nodes:

            break

        last_face = path[-1][0] if path else None

        for move in MOVE_NAMES:

            face = move[0]

            if face == last_face:
                continue

            new_state = apply_move(state, move)

            if new_state not in visited:

                visited.add(new_state)

                queue.append(
                    (new_state, path + [move])
                )

    return None, nodes


# -------------------- IDDFS ALGORITHM ----------------------

def iddfs(start_state, max_depth=6, max_nodes=100000):

    nodes = 0

    for limit in range(max_depth + 1):

        def depth_search(state, depth, last_face, path):

            nonlocal nodes

            nodes += 1

            if nodes > max_nodes:
                return None

            if state == SOLVED_STATE:
                return path.copy()

            if depth == limit:
                return None

            for move in MOVE_NAMES:

                face = move[0]

                if face == last_face:
                    continue

                new_state = apply_move(state, move)

                path.append(move)

                result = depth_search(
                    new_state,
                    depth + 1,
                    face,
                    path
                )

                if result is not None:
                    return result

                path.pop()

            return None

        result = depth_search(
            start_state,
            0,
            None,
            []
        )

        if result is not None:

            return result, nodes

        if nodes > max_nodes:
            break

    return None, nodes


# -------------------- A* ALGORITHM -------------------------

# A* is included for comparison.
# Its memory requirement grows rapidly.

def astar(start_state, max_nodes=100000):

    counter = 0

    initial_h = heuristic(start_state)

    open_list = [
        (initial_h, 0, counter, start_state, [])
    ]

    best_g = {start_state: 0}

    nodes = 0

    while open_list:

        f, g, _, state, path = heapq.heappop(open_list)

        if g != best_g.get(state):
            continue

        nodes += 1

        if state == SOLVED_STATE:

            return path, nodes

        if nodes >= max_nodes:

            break

        last_face = path[-1][0] if path else None

        for move in MOVE_NAMES:

            face = move[0]

            if face == last_face:
                continue

            new_state = apply_move(state, move)

            new_g = g + 1

            if new_g < best_g.get(new_state, float("inf")):

                best_g[new_state] = new_g

                counter += 1

                new_path = path + [move]

                new_f = new_g + heuristic(new_state)

                heapq.heappush(
                    open_list,
                    (
                        new_f,
                        new_g,
                        counter,
                        new_state,
                        new_path
                    )
                )

    return None, nodes


# -------------------- PERFORMANCE REPORT -------------------

def print_statistics(statistics, solution):

    print("\n========== PERFORMANCE REPORT ==========")

    print("Nodes explored:", statistics.nodes)

    print("IDA* iterations:", statistics.iterations)

    print(
        "Execution time:",
        round(statistics.elapsed(), 6),
        "seconds"
    )

    if solution is not None:

        print("Solution length:", len(solution))

    else:

        print("No solution found within search limits.")

    print("========================================")


# -------------------- SELF TESTS ----------------------------

def run_tests():

    print("\nRunning cube engine tests...")

    for face in FACES:

        # Four clockwise turns must restore the cube.

        state = SOLVED_STATE

        for _ in range(4):

            state = apply_move(state, face)

        assert state == SOLVED_STATE

        # Clockwise followed by inverse.

        state = apply_move(SOLVED_STATE, face)

        state = apply_move(state, face + "'")

        assert state == SOLVED_STATE

        # Two half-turns must restore the cube.

        state = apply_move(SOLVED_STATE, face + "2")

        state = apply_move(state, face + "2")

        assert state == SOLVED_STATE

    # Every generated move must preserve sticker counts.

    for move in MOVE_NAMES:

        state = apply_move(SOLVED_STATE, move)

        assert validate_cube(state)

    print("All cube engine tests passed.")


# -------------------- MAIN PROGRAM --------------------------

def main():

    print("\n========================================")
    print("       RUBIK'S CUBE AI SOLVER")
    print("========================================")

    print("\nAlgorithm: IDA*")
    print("Search metric: HTM")
    print("Representation: 54 Facelets")

    run_tests()

    print("\nChoose input method:")

    print("1. Generate random scramble")
    print("2. Enter your own scramble")

    choice = input("\nEnter choice (1/2): ").strip()

    if choice == "2":

        scramble_text = input(
            "\nEnter scramble (example: R U R' U'): "
        )

        try:

            scramble = parse_moves(scramble_text)

        except ValueError as error:

            print(error)
            return

    else:

        scramble = generate_scramble(SCRAMBLE_LENGTH)

    print("\nScramble:")

    print(" ".join(scramble))

    scrambled_state = apply_moves(
        SOLVED_STATE,
        scramble
    )

    if not validate_cube(scrambled_state):

        print("Invalid cube state.")
        return

    display_cube(scrambled_state)

    if is_solved(scrambled_state):

        print("Cube is already solved.")
        return

    print("\nStarting IDA* search...")

    solution, statistics = ida_star(
        scrambled_state,
        max_depth=MAX_SEARCH_DEPTH,
        max_nodes=MAX_NODES
    )

    if solution is None:

        print("\nUnable to complete the search.")

        print(
            "Try a shorter scramble or increase MAX_NODES."
        )

        print_statistics(statistics, None)

        return

    print("\n========== SOLUTION ==========")

    print(" ".join(solution))

    print("Number of moves:", len(solution))

    # Verify the generated solution.

    final_state = apply_moves(
        scrambled_state,
        solution
    )

    print("\nSolution Verification:")

    if is_solved(final_state):

        print("SUCCESS: Cube solved correctly.")

    else:

        print("ERROR: Solution verification failed.")

    print_statistics(statistics, solution)


# -------------------- EXECUTION -----------------------------

if __name__ == "__main__":

    main()
