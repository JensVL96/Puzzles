import time

# --- Board setup ---
board_size = 11

board = [["." for _ in range(board_size)] for _ in range(board_size)]

top  = [1,1,3,1,6,2,0,2,5,3,1]
side = [4,0,0,3,4,2,1,2,0,7,2]

ship_counts = {
    5: 1,
    4: 1,
    3: 2,
    2: 3,
    1: 4,
}

board[7][4] = "F"  # y,x
# forced_cells = {(7, 9)}

counter = 0

solutions = set()
visited_states = set()

LENGTH_ORDER = sorted(ship_counts.keys(), reverse=True)
FULL_ROW_MASK = (1 << board_size) - 1
ZERO_LINE_MASKS = [0] * board_size
FORCED_CELLS = []

# --- Helpers ---

def set_forced_ship(r, c):
    # Mark a coordinate as a forced ship cell from puzzle clues.
    board[r][c] = "F"

def cell_allowed_by_zero_lines(r, c):
    # Rows/columns with clue 0 cannot contain ship cells.
    return side[r] != 0 and top[c] != 0

def remaining_ship_cells(ships):
    # Total number of ship cells that still need to be placed.
    return sum(length * count for length, count in ships.items())

def check_counts(row_hits, col_hits):
    # Final validation: every row and column must exactly match the given clues.
    for r, count in enumerate(side):
        if row_hits[r] != count:
            return False

    for c, count in enumerate(top):
        if col_hits[c] != count:
            return False
    return True

def check_partial(row_hits, col_hits, blocked_rows, ships_remaining):
    # Early pruning with both lower and upper feasibility bounds.
    # Reject if a line already exceeds target, or if it can no longer reach target.
    for r, target in enumerate(side):
        if row_hits[r] > target:
            return False
        row_open = (FULL_ROW_MASK ^ blocked_rows[r]).bit_count()
        if row_hits[r] + row_open < target:
            return False

    for c, target in enumerate(top):
        if col_hits[c] > target:
            return False
        col_open = 0
        col_bit = 1 << c
        for r in range(board_size):
            if blocked_rows[r] & col_bit == 0:
                col_open += 1
        if col_hits[c] + col_open < target:
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

def build_zero_line_masks():
    for r in range(board_size):
        mask = 0
        for c in range(board_size):
            if not cell_allowed_by_zero_lines(r, c):
                mask |= 1 << c
        ZERO_LINE_MASKS[r] = mask

def extract_forced_cells():
    forced = []
    for r in range(board_size):
        for c in range(board_size):
            if board[r][c] == "F":
                forced.append((r, c))
    return forced

def placement_to_masks(cells):
    ship_masks = [0] * board_size
    blocked_masks = [0] * board_size

    for r, c in cells:
        ship_masks[r] |= 1 << c
        for dr in (-1, 0, 1):
            nr = r + dr
            if not (0 <= nr < board_size):
                continue
            for dc in (-1, 0, 1):
                nc = c + dc
                if 0 <= nc < board_size:
                    blocked_masks[nr] |= 1 << nc

    row_adds = [(r, mask.bit_count()) for r, mask in enumerate(ship_masks) if mask]
    col_adds = [0] * board_size
    for _, c in cells:
        col_adds[c] += 1

    col_adds = [(c, cnt) for c, cnt in enumerate(col_adds) if cnt]
    touched_rows = [r for r, mask in enumerate(blocked_masks) if mask]

    return {
        "cells": cells,
        "ship_masks": ship_masks,
        "blocked_masks": blocked_masks,
        "row_adds": row_adds,
        "col_adds": col_adds,
        "touched_rows": touched_rows,
    }

def build_placements_by_length():
    placements = {length: [] for length in LENGTH_ORDER}

    for length in LENGTH_ORDER:
        seen_keys = set()

        for r in range(board_size):
            for c in range(board_size - length + 1):
                cells = tuple((r, c + i) for i in range(length))
                if any(not cell_allowed_by_zero_lines(rr, cc) for rr, cc in cells):
                    continue
                if cells not in seen_keys:
                    seen_keys.add(cells)
                    placements[length].append(placement_to_masks(cells))

        if length > 1:
            for r in range(board_size - length + 1):
                for c in range(board_size):
                    cells = tuple((r + i, c) for i in range(length))
                    if any(not cell_allowed_by_zero_lines(rr, cc) for rr, cc in cells):
                        continue
                    if cells not in seen_keys:
                        seen_keys.add(cells)
                        placements[length].append(placement_to_masks(cells))

    return placements

def placement_fits(placement, blocked_rows, row_hits, col_hits):
    for r, ship_mask in enumerate(placement["ship_masks"]):
        if ship_mask and (blocked_rows[r] & ship_mask):
            return False

    for r, add in placement["row_adds"]:
        if row_hits[r] + add > side[r]:
            return False

    for c, add in placement["col_adds"]:
        if col_hits[c] + add > top[c]:
            return False

    return True

def apply_placement(placement, occupied_rows, blocked_rows, row_hits, col_hits):
    changed_blocked = []
    changed_occupied = []

    for r in placement["touched_rows"]:
        old = blocked_rows[r]
        new = old | placement["blocked_masks"][r]
        if new != old:
            changed_blocked.append((r, old))
            blocked_rows[r] = new

    for r in range(board_size):
        ship_mask = placement["ship_masks"][r]
        if ship_mask:
            old = occupied_rows[r]
            new = old | ship_mask
            if new != old:
                changed_occupied.append((r, old))
                occupied_rows[r] = new

    for r, add in placement["row_adds"]:
        row_hits[r] += add
    for c, add in placement["col_adds"]:
        col_hits[c] += add

    return changed_blocked, changed_occupied

def undo_placement(placement, occupied_rows, blocked_rows, row_hits, col_hits, changed_blocked, changed_occupied):
    for c, add in placement["col_adds"]:
        col_hits[c] -= add
    for r, add in placement["row_adds"]:
        row_hits[r] -= add

    for r, old in reversed(changed_occupied):
        occupied_rows[r] = old
    for r, old in reversed(changed_blocked):
        blocked_rows[r] = old

def occupied_rows_to_board_tuple(occupied_rows):
    rows = []
    for r in range(board_size):
        row_chars = []
        row_mask = occupied_rows[r]
        for c in range(board_size):
            row_chars.append("X" if (row_mask >> c) & 1 else ".")
        rows.append("".join(row_chars))
    return tuple(rows)

def generate_largest_ship_candidates(occupied_rows, blocked_rows, row_hits, col_hits, ships, placements_by_length):
    largest_length = max(ships)
    remaining_ships = reduce_ship_inventory(ships, largest_length)

    candidates = []
    for placement in placements_by_length[largest_length]:
        if not placement_fits(placement, blocked_rows, row_hits, col_hits):
            continue

        changed_blocked, changed_occupied = apply_placement(
            placement, occupied_rows, blocked_rows, row_hits, col_hits
        )
        if check_partial(row_hits, col_hits, blocked_rows, remaining_ships):
            candidates.append(occupied_rows_to_board_tuple(occupied_rows))

        undo_placement(
            placement, occupied_rows, blocked_rows, row_hits, col_hits,
            changed_blocked, changed_occupied,
        )

    return largest_length, remaining_ships, candidates

def print_largest_ship_candidates(largest_length, candidate_boards):
    print(f"\nLargest ship length: {largest_length}")
    print(f"Possible boards with only this ship placed: {len(candidate_boards)}\n")
    for idx, board_tuple in enumerate(candidate_boards, 1):
        print(f"Candidate {idx}:")
        print_board(tuple_to_board(board_tuple))
        print()

# --- Solver ---

def solve_all(occupied_rows, blocked_rows, row_hits, col_hits, ships, placements_by_length):
    # In-place backtracking solver with fast bitmask checks and undo operations.
    if not ships:
        if not check_counts(row_hits, col_hits):
            return

        for r, c in FORCED_CELLS:
            if (occupied_rows[r] & (1 << c)) == 0:
                return

        solutions.add(occupied_rows_to_board_tuple(occupied_rows))
        return

    state_key = (tuple(occupied_rows), tuple(ships.get(length, 0) for length in LENGTH_ORDER))
    if state_key in visited_states:
        return
    visited_states.add(state_key)

    length = max(ships)
    new_ships = reduce_ship_inventory(ships, length)
    for placement in placements_by_length[length]:
        if not placement_fits(placement, blocked_rows, row_hits, col_hits):
            continue

        changed_blocked, changed_occupied = apply_placement(
            placement, occupied_rows, blocked_rows, row_hits, col_hits
        )

        if check_partial(row_hits, col_hits, blocked_rows, new_ships):
            solve_all(occupied_rows, blocked_rows, row_hits, col_hits, new_ships, placements_by_length)

        undo_placement(
            placement, occupied_rows, blocked_rows, row_hits, col_hits,
            changed_blocked, changed_occupied,
        )

build_zero_line_masks()
FORCED_CELLS = extract_forced_cells()
placements_by_length = build_placements_by_length()

initial_occupied_rows = [0] * board_size
initial_blocked_rows = ZERO_LINE_MASKS[:]
initial_row_hits = [0] * board_size
initial_col_hits = [0] * board_size

for r, c in FORCED_CELLS:
    bit = 1 << c
    initial_occupied_rows[r] |= bit
    initial_row_hits[r] += 1
    initial_col_hits[c] += 1
    for dr in (-1, 0, 1):
        nr = r + dr
        if not (0 <= nr < board_size):
            continue
        for dc in (-1, 0, 1):
            nc = c + dc
            if 0 <= nc < board_size:
                initial_blocked_rows[nr] |= 1 << nc

initial_ships = ship_counts.copy()

largest_length, ships_after_largest, largest_candidates = generate_largest_ship_candidates(
    initial_occupied_rows,
    initial_blocked_rows,
    initial_row_hits,
    initial_col_hits,
    initial_ships,
    placements_by_length,
)
print_largest_ship_candidates(largest_length, largest_candidates)

start_time = time.perf_counter()
for candidate in largest_candidates:
    occupied_rows = [0] * board_size
    blocked_rows = ZERO_LINE_MASKS[:]
    row_hits = [0] * board_size
    col_hits = [0] * board_size

    for r, row in enumerate(candidate):
        mask = 0
        for c, ch in enumerate(row):
            if ch == "X":
                mask |= 1 << c
                row_hits[r] += 1
                col_hits[c] += 1
        occupied_rows[r] = mask

    for r in range(board_size):
        row_mask = occupied_rows[r]
        c = 0
        while c < board_size:
            if (row_mask >> c) & 1:
                for dr in (-1, 0, 1):
                    nr = r + dr
                    if not (0 <= nr < board_size):
                        continue
                    for dc in (-1, 0, 1):
                        nc = c + dc
                        if 0 <= nc < board_size:
                            blocked_rows[nr] |= 1 << nc
            c += 1

    solve_all(occupied_rows, blocked_rows, row_hits, col_hits, ships_after_largest, placements_by_length)
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