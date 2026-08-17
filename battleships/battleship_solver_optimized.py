from itertools import product, permutations, combinations
import time

# --- Board setup ---
board_size = 10

board = [["." for _ in range(board_size)] for _ in range(board_size)]

top  = [1,3,1,3,5,0,3,1,1,2]
side = [0,6,2,1,0,5,1,2,2,1]

ship_counts = {
    4: 1,
    3: 2,
    2: 3,
    1: 4,
}

# board[0][5] = "F" # y,x
# forced_cells = {(7, 9)}

counter = 0

solutions = set()
visited_states = set()

# --- Helpers ---

def set_forced_ship(r, c):
    # Mark a coordinate as a forced ship cell from puzzle clues.
    board[r][c] = "F"

def in_bounds(r, c):
    # Return True only for coordinates that are inside the 10x10 board.
    return 0 <= r < board_size and 0 <= c < board_size

def cell_allowed_by_zero_lines(r, c):
    # Rows/columns with clue 0 cannot contain ship cells.
    return side[r] != 0 and top[c] != 0

def can_place(board, r, c, length, horizontal):
    # Validate whether a ship can be placed at (r, c) with the given orientation.
    # The placement must stay in bounds, avoid overlap, and satisfy the no-touching rule.
    for i in range(length):
        rr = r + (0 if horizontal else i)
        cc = c + (i if horizontal else 0)
        if not in_bounds(rr, cc):
            return False
        if not cell_allowed_by_zero_lines(rr, cc):
            return False
        if board[rr][cc] == "X":
            return False
        # check surrounding cells
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if not in_bounds(nr, nc):
                    continue
                # Ignore cells that are part of THIS ship placement
                if horizontal:
                    if nr == r and c <= nc < c + length:
                        continue
                else:
                    if nc == c and r <= nr < r + length:
                        continue

                if board[nr][nc] == "X":
                    return False
    return True

def place_ship(board, r, c, length, horizontal):
    # Return a copied board with one ship painted as "X" at the requested position.
    # Copying keeps recursion side-effect free for backtracking.
    new_board = [row[:] for row in board]
    for i in range(length):
        rr = r + (0 if horizontal else i)
        cc = c + (i if horizontal else 0)
        new_board[rr][cc] = "X"
    return new_board

def remaining_ship_cells(ships):
    # Total number of ship cells that still need to be placed.
    return sum(length * count for length, count in ships.items())

def compute_line_stats(board):
    # Compute per-row/column current ship counts and still-available cells.
    row_hits = [0] * board_size
    col_hits = [0] * board_size
    row_open = [0] * board_size
    col_open = [0] * board_size

    for r in range(board_size):
        for c in range(board_size):
            if board[r][c] == "X":
                row_hits[r] += 1
                col_hits[c] += 1
            elif cell_allowed_by_zero_lines(r, c):
                row_open[r] += 1
                col_open[c] += 1

    return row_hits, col_hits, row_open, col_open

def check_counts(board):
    # Final validation: every row and column must exactly match the given clues.
    for r, count in enumerate(side):
        if sum(1 for cell in board[r] if cell == "X") != count:
            return False

    for c, count in enumerate(top):
        if sum(1 for r in range(board_size) if board[r][c] == "X") != count:
            return False
    return True

def check_partial(board, ships_remaining):
    # Early pruning with both lower and upper feasibility bounds.
    # Reject if a line already exceeds target, or if it can no longer reach target.
    row_hits, col_hits, row_open, col_open = compute_line_stats(board)

    for r, target in enumerate(side):
        if row_hits[r] > target:
            return False
        if row_hits[r] + row_open[r] < target:
            return False

    for c, target in enumerate(top):
        if col_hits[c] > target:
            return False
        if col_hits[c] + col_open[c] < target:
            return False

    # Global cell-balance check: remaining fleet cells must match remaining deficits.
    placed_cells = sum(row_hits)
    remaining_needed = sum(side) - placed_cells
    if remaining_needed != remaining_ship_cells(ships_remaining):
        return False

    return True

def reduce_ship_inventory(ships, length):
    # Return a copied ship inventory after consuming one ship of `length`.
    new_ships = ships.copy()
    if new_ships[length] == 1:
        del new_ships[length]
    else:
        new_ships[length] -= 1
    return new_ships

def board_to_tuple(board):
    # Immutable representation useful for deduplication and storage.
    return tuple("".join(row) for row in board)

def tuple_to_board(board_tuple):
    # Convert immutable tuple form back to mutable row/char lists.
    return [list(row) for row in board_tuple]

def print_board(board):
    for row in board:
        print("".join(row))

def generate_candidates_for_length(board, length, ships_after_placing_one):
    # Enumerate valid next boards for placing one ship of a specific length.
    candidates = []
    seen = set()

    # Horizontal placements: start column must allow full ship length.
    for r in range(board_size):
        for c in range(board_size - length + 1):
            if can_place(board, r, c, length, True):
                new_board = place_ship(board, r, c, length, True)
                if check_partial(new_board, ships_after_placing_one):
                    board_key = board_to_tuple(new_board)
                    if board_key not in seen:
                        seen.add(board_key)
                        candidates.append(board_key)

    # Vertical placements: start row must allow full ship length.
    for r in range(board_size - length + 1):
        for c in range(board_size):
            if can_place(board, r, c, length, False):
                new_board = place_ship(board, r, c, length, False)
                if check_partial(new_board, ships_after_placing_one):
                    board_key = board_to_tuple(new_board)
                    if board_key not in seen:
                        seen.add(board_key)
                        candidates.append(board_key)

    return candidates

def generate_largest_ship_candidates(board, ships):
    # Build all valid boards that place exactly one largest ship.
    largest_length = max(ships)
    remaining_ships = reduce_ship_inventory(ships, largest_length)
    candidate_boards = generate_candidates_for_length(board, largest_length, remaining_ships)
    return largest_length, remaining_ships, candidate_boards

def print_largest_ship_candidates(largest_length, candidate_boards):
    print(f"\nLargest ship length: {largest_length}")
    print(f"Possible boards with only this ship placed: {len(candidate_boards)}\n")
    for idx, board_tuple in enumerate(candidate_boards, 1):
        print(f"Candidate {idx}:")
        print_board(tuple_to_board(board_tuple))
        print()

# --- Solver ---

def solve_all(board, ships):
    # Backtracking solver:
    # 1) If no ships remain, validate full constraints and store unique solutions.
    # 2) Otherwise, pick the largest remaining ship and try all legal placements.
    # 3) Recurse only when partial row/column clues are still satisfiable.
    if not ships:
        if check_counts(board) and all(
            board[r][c] == "X"
            for r in range(board_size)
            for c in range(board_size)
            if original_board[r][c] == "F"
        ):
            solutions.add(board_to_tuple(board))
        return

    state_key = (board_to_tuple(board), tuple(sorted(ships.items())))
    if state_key in visited_states:
        return
    visited_states.add(state_key)

    length = max(ships)
    new_ships = reduce_ship_inventory(ships, length)
    candidates = generate_candidates_for_length(board, length, new_ships)
    if not candidates:
        return

    for candidate in candidates:
        solve_all(tuple_to_board(candidate), new_ships)

original_board = [row[:] for row in board] 
largest_length, ships_after_largest, largest_candidates = generate_largest_ship_candidates(original_board, ship_counts)
print_largest_ship_candidates(largest_length, largest_candidates)

start_time = time.perf_counter()
for candidate in largest_candidates:
    solve_all(tuple_to_board(candidate), ships_after_largest)
end_time = time.perf_counter()

print(f"\nRuntime: {end_time - start_time:.4f} seconds")
if solutions:
    print(f"\nFound {len(solutions)} unique solutions:\n")
    for idx, sol in enumerate(solutions, 1):
        print(f"Solution {idx}:")
        for row in sol:
            print(row)
        print()
else:
    print("No solution found")