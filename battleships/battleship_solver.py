from itertools import product, permutations, combinations
import time

# --- Board setup ---
board_size = 10

board = [["." for _ in range(board_size)] for _ in range(board_size)]

top  = [1,2,1,3,1,5,3,3,1,0]
side = [1,4,0,4,2,3,1,2,1,2]

ship_counts = {
    4: 1,
    3: 2,
    2: 3,
    1: 4,
}

board[0][5] = "F" # y,x
# forced_cells = {(7, 9)}

counter = 0

solutions = set()

# --- Helpers ---

def set_forced_ship(r, c):
    # Mark a coordinate as a forced ship cell from puzzle clues.
    board[r][c] = "F"

def in_bounds(r, c):
    # Return True only for coordinates that are inside the 10x10 board.
    return 0 <= r < board_size and 0 <= c < board_size

def can_place(board, r, c, length, horizontal):
    # Validate whether a ship can be placed at (r, c) with the given orientation.
    # The placement must stay in bounds, avoid overlap, and satisfy the no-touching rule.
    for i in range(length):
        rr = r + (0 if horizontal else i)
        cc = c + (i if horizontal else 0)
        if not in_bounds(rr, cc):
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
    # Early pruning: reject states that already exceed row/column clue limits.
    # If a partial board is already too full in any line, deeper search is pointless.
    for r, target in enumerate(side):
        if sum(1 for cell in board[r] if cell == "X") > target:
            return False
    for c, target in enumerate(top):
        if sum(1 for r in range(board_size) if board[r][c] == "X") > target:
            return False
    return True

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
            # Convert board to immutable tuple form
            board_tuple = tuple("".join(row) for row in board)
            solutions.add(board_tuple)
        return

    lengths = sorted(ships.keys(), reverse=True)
    length = lengths[0]
    count = ships[length]

    new_ships = ships.copy()
    if count == 1:
        del new_ships[length]
    else:
        new_ships[length] -= 1

    for r, c in product(range(board_size), repeat=2):
        for horizontal in [True, False]:
            if can_place(board, r, c, length, horizontal):
                new_board = place_ship(board, r, c, length, horizontal)
                if check_partial(new_board, new_ships):
                    solve_all(new_board, new_ships)

original_board = [row[:] for row in board] 
start_time = time.perf_counter()
solution = solve_all(original_board, ship_counts)
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