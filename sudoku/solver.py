from itertools import combinations


def get_candidates(board):
    """Returns {(row, col): set of valid values} for all empty cells."""
    candidates = {}
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0 or isinstance(board[r][c], list):
                used = set()
                used.update(v for v in board[r] if isinstance(v, int))
                used.update(board[i][c] for i in range(9) if isinstance(board[i][c], int))
                br, bc = (r // 3) * 3, (c // 3) * 3
                used.update(
                    board[br + i][bc + j]
                    for i in range(3) for j in range(3)
                    if isinstance(board[br + i][bc + j], int)
                )
                candidates[(r, c)] = set(range(1, 10)) - used
    return candidates


def sees(a, b):
    return (a[0] == b[0] or a[1] == b[1] or
            (a[0] // 3 == b[0] // 3 and a[1] // 3 == b[1] // 3))

def shared_units(cell1, cell2):
    r1, c1 = cell1
    r2, c2 = cell2
    units = []
    if r1 == r2:
        units.append([(r1, c) for c in range(9)])
    if c1 == c2:
        units.append([(r, c1) for r in range(9)])
    if r1 // 3 == r2 // 3 and c1 // 3 == c2 // 3:
        br, bc = (r1 // 3) * 3, (c1 // 3) * 3
        units.append([(br + i, bc + j) for i in range(3) for j in range(3)])
    return units

def all_units():
    units = []
    for i in range(9):
        units.append([(i, c) for c in range(9)])
        units.append([(r, i) for r in range(9)])
        units.append([(r, c)
                       for r in range((i // 3) * 3, (i // 3) * 3 + 3)
                       for c in range((i % 3) * 3, (i % 3) * 3 + 3)])
    return units


def pencil(board):
    """Fill candidates for all empty cells based on elimination."""
    candidates = get_candidates(board)
    for (r, c), vals in candidates.items():
        if board[r][c] == 0:
            board[r][c] = sorted(vals)


# Placers return (row, col, val) — the cell is solved.
# Eliminators return [(row, col, val), ...] — remove val from candidates in those cells.

def naked_single(board): #Forced move
    # Check if any row, column, or block has only one candidate for a cell
    candidates = get_candidates(board)
    for (r, c), vals in candidates.items():
        if len(vals) == 1:
            return (r, c, vals.pop())

def hidden_single(board):
    # Check if any number can only go in one cell in a row, column, or block
    candidates = get_candidates(board)
    for num in range(1, 10):
        # Check rows
        for r in range(9):
            positions = [(r, c) for c in range(9) if num in candidates.get((r, c), set())]
            if len(positions) == 1:
                return (positions[0][0], positions[0][1], num)
        # Check columns
        for c in range(9):
            positions = [(r, c) for r in range(9) if num in candidates.get((r, c), set())]
            if len(positions) == 1:
                return (positions[0][0], positions[0][1], num)
        # Check blocks
        for br in range(3):
            for bc in range(3):
                positions = [
                    (br * 3 + r, bc * 3 + c)
                    for r in range(3) for c in range(3)
                    if num in candidates.get((br * 3 + r, bc * 3 + c), set())
                ]
                if len(positions) == 1:
                    return (positions[0][0], positions[0][1], num)

def intersections(board):
    valid = get_candidates(board)
    eliminations = [
        (r, c, v)
        for (r, c), valid_vals in valid.items()
        if isinstance(board[r][c], list)
        for v in board[r][c]
        if v not in valid_vals
    ]
    return eliminations if eliminations else None

def locked_sets(board):
    candidates = get_candidates(board)

    for n in range(2, 5):  # pairs, triples, quads
        for unit in all_units():
            unit_cells = [cell for cell in unit if cell in candidates]
            for combo in combinations(unit_cells, n):
                combined = set.union(*(candidates[cell] for cell in combo))
                if len(combined) == n:
                    eliminations = []
                    for cell in unit_cells:
                        if cell not in combo:
                            for val in combined:
                                if val in candidates[cell]:
                                    eliminations.append((cell[0], cell[1], val))
                    if eliminations:
                        return eliminations

def forced_moves(board):
    pass

def pinned_squares(board):
    pass

def intersection_removal(board):
    candidates = get_candidates(board)
    for num in range(1, 10):

        # Direction 1: box -> row/col
        # If all candidates for a number in a box share a row or column,
        # eliminate from the rest of that row or column outside the box.
        for br in range(3):
            for bc in range(3):
                positions = [
                    (br * 3 + r, bc * 3 + c)
                    for r in range(3) for c in range(3)
                    if num in candidates.get((br * 3 + r, bc * 3 + c), set())
                ]
                if len(positions) > 1:
                    rows = {p[0] for p in positions}
                    cols = {p[1] for p in positions}
                    if len(rows) == 1:
                        row = rows.pop()
                        eliminations = [
                            (row, c, num) for c in range(9)
                            if (row, c) not in positions
                            and num in candidates.get((row, c), set())
                        ]
                        if eliminations:
                            return eliminations
                    elif len(cols) == 1:
                        col = cols.pop()
                        eliminations = [
                            (r, col, num) for r in range(9)
                            if (r, col) not in positions
                            and num in candidates.get((r, col), set())
                        ]
                        if eliminations:
                            return eliminations

        # Direction 2: row/col -> box
        # If all candidates for a number in a row or column are within the same box,
        # eliminate from the rest of that box.
        for r in range(9):
            positions = [(r, c) for c in range(9) if num in candidates.get((r, c), set())]
            if len(positions) > 1:
                boxes = {(p[0] // 3, p[1] // 3) for p in positions}
                if len(boxes) == 1:
                    br, bc = boxes.pop()
                    eliminations = [
                        (br * 3 + i, bc * 3 + j, num)
                        for i in range(3) for j in range(3)
                        if (br * 3 + i, bc * 3 + j) not in positions
                        and num in candidates.get((br * 3 + i, bc * 3 + j), set())
                    ]
                    if eliminations:
                        return eliminations

        for c in range(9):
            positions = [(r, c) for r in range(9) if num in candidates.get((r, c), set())]
            if len(positions) > 1:
                boxes = {(p[0] // 3, p[1] // 3) for p in positions}
                if len(boxes) == 1:
                    br, bc = boxes.pop()
                    eliminations = [
                        (br * 3 + i, bc * 3 + j, num)
                        for i in range(3) for j in range(3)
                        if (br * 3 + i, bc * 3 + j) not in positions
                        and num in candidates.get((br * 3 + i, bc * 3 + j), set())
                    ]
                    if eliminations:
                        return eliminations

def x_wing(board):
    candidates = get_candidates(board)
    for num in range(1, 10):
        # Check rows
        row_positions = {
            r: [(r, c) for c in range(9) if num in candidates.get((r, c), set())]
            for r in range(9)
        }
        row_positions = {r: pos for r, pos in row_positions.items() if len(pos) == 2}

        for r1, r2 in combinations(row_positions.keys(), 2):
            cols1 = {pos[1] for pos in row_positions[r1]}
            cols2 = {pos[1] for pos in row_positions[r2]}
            if cols1 == cols2:
                eliminations = [
                    (r, c, num)
                    for r in range(9) if r not in (r1, r2)
                    for c in cols1
                    if num in candidates.get((r, c), set())
                ]
                if eliminations:
                    return eliminations

        # Check columns
        col_positions = {
            c: [(r, c) for r in range(9) if num in candidates.get((r, c), set())]
            for c in range(9)
        }
        col_positions = {c: pos for c, pos in col_positions.items() if len(pos) == 2}

        for c1, c2 in combinations(col_positions.keys(), 2):
            rows1 = {pos[0] for pos in col_positions[c1]}
            rows2 = {pos[0] for pos in col_positions[c2]}
            if rows1 == rows2:
                eliminations = [
                    (r, c, num)
                    for c in range(9) if c not in (c1, c2)
                    for r in rows1
                    if num in candidates.get((r, c), set())
                ]
                if eliminations:
                    return eliminations

def swordfish(board):
    candidates = get_candidates(board)
    for num in range(1, 10):
        # Check rows
        row_positions = {
            r: [(r, c) for c in range(9) if num in candidates.get((r, c), set())]
            for r in range(9)
        }
        row_positions = {r: pos for r, pos in row_positions.items() if 2 <= len(pos) <= 3}

        for r1, r2, r3 in combinations(row_positions.keys(), 3):
            cols = {pos[1] for pos in row_positions[r1] + row_positions[r2] + row_positions[r3]}
            if len(cols) == 3:
                eliminations = [
                    (r, c, num)
                    for r in range(9) if r not in (r1, r2, r3)
                    for c in cols
                    if num in candidates.get((r, c), set())
                ]
                if eliminations:
                    return eliminations

        # Check columns
        col_positions = {
            c: [(r, c) for r in range(9) if num in candidates.get((r, c), set())]
            for c in range(9)
        }
        col_positions = {c: pos for c, pos in col_positions.items() if 2 <= len(pos) <= 3}

        for c1, c2, c3 in combinations(col_positions.keys(), 3):
            rows = {pos[0] for pos in col_positions[c1] + col_positions[c2] + col_positions[c3]}
            if len(rows) == 3:
                eliminations = [
                    (r, c, num)
                    for c in range(9) if c not in (c1, c2, c3)
                    for r in rows
                    if num in candidates.get((r, c), set())
                ]
                if eliminations:
                    return eliminations

def remote_pairs(board):
    candidates = get_candidates(board)
    bivalue = {cell: frozenset(vals) for cell, vals in candidates.items() if len(vals) == 2}

    pair_groups = {}
    for cell, pair in bivalue.items():
        pair_groups.setdefault(pair, []).append(cell)

    for pair, cells in pair_groups.items():
        if len(cells) < 4:
            continue

        cell_set = set(cells)

        for start in cells:
            # BFS to find distance to all other cells in this pair group
            dist = {start: 0}
            queue = [start]
            while queue:
                curr = queue.pop(0)
                for neighbor in cells:
                    if neighbor not in dist and sees(curr, neighbor):
                        dist[neighbor] = dist[curr] + 1
                        queue.append(neighbor)

            # Odd distance >= 3 means even number of cells in the chain,
            # start and end hold opposite values — any cell seeing both can't hold either
            for end, d in dist.items():
                if d < 3 or d % 2 == 0:
                    continue
                eliminations = []
                for cell, vals in candidates.items():
                    if cell in cell_set:
                        continue
                    if sees(cell, start) and sees(cell, end):
                        for v in pair:
                            if v in vals:
                                eliminations.append((cell[0], cell[1], v))
                if eliminations:
                    return eliminations

def unique_rectangle_12(board):
    candidates = get_candidates(board)

    # Group bivalue cells by their pair
    bivalue_by_pair = {}
    for cell, vals in candidates.items():
        if len(vals) == 2:
            bivalue_by_pair.setdefault(frozenset(vals), []).append(cell)

    for pair, bvcells in bivalue_by_pair.items():
        if len(bvcells) < 3:
            continue

        # Type 1: find 3 bivalue corners — the 4th must complete a valid rectangle
        for i, j, k in combinations(range(len(bvcells)), 3):
            three = [bvcells[i], bvcells[j], bvcells[k]]
            rows = {c[0] for c in three}
            cols = {c[1] for c in three}

            if len(rows) != 2 or len(cols) != 2:
                continue

            r1, r2 = sorted(rows)
            c1, c2 = sorted(cols)

            # Rectangle must span exactly 2 boxes
            if not ((r1 // 3 == r2 // 3) ^ (c1 // 3 == c2 // 3)):
                continue

            all_corners = {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}
            fourth_cell = (all_corners - set(three)).pop()
            ec = candidates.get(fourth_cell, set())

            if pair.issubset(ec) and len(ec) > 2:
                r, c = fourth_cell
                eliminations = [(r, c, v) for v in pair if v in ec]
                if eliminations:
                    return eliminations

    # Type 2: 2 bivalue corners + 2 corners with pair + same single extra candidate
    for r1 in range(9):
        for r2 in range(r1 + 1, 9):
            for c1 in range(9):
                for c2 in range(c1 + 1, 9):
                    if not ((r1 // 3 == r2 // 3) ^ (c1 // 3 == c2 // 3)):
                        continue

                    corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
                    cvals = [candidates.get(corner, set()) for corner in corners]

                    for fi, fj in combinations(range(4), 2):
                        ri = [i for i in range(4) if i not in (fi, fj)]
                        fv = [cvals[fi], cvals[fj]]
                        rv = [cvals[ri[0]], cvals[ri[1]]]

                        if len(fv[0]) != 2 or fv[0] != fv[1]:
                            continue

                        pair = fv[0]
                        if not (pair.issubset(rv[0]) and pair.issubset(rv[1])):
                            continue

                        extra = rv[0] - pair
                        if len(extra) != 1 or extra != rv[1] - pair:
                            continue

                        x = next(iter(extra))
                        roof = [corners[ri[0]], corners[ri[1]]]

                        eliminations = [
                            (r, c, x) for (r, c), vals in candidates.items()
                            if (r, c) not in roof
                            and x in vals
                            and sees((r, c), roof[0])
                            and sees((r, c), roof[1])
                        ]
                        if eliminations:
                            return eliminations

def hidden_sets(board):
    candidates = get_candidates(board)

    for n in range(2, 5):  # pairs, triples, quads
        for unit in all_units():
            unit_cells = [cell for cell in unit if cell in candidates]
            if len(unit_cells) < n:
                continue

            all_vals = set.union(*(candidates[cell] for cell in unit_cells))

            for val_combo in combinations(all_vals, n):
                val_set = set(val_combo)

                # Cells that contain at least one of these N values
                cells_with_vals = [
                    cell for cell in unit_cells
                    if val_set & candidates[cell]
                ]

                if len(cells_with_vals) == n:
                    # Hidden set: eliminate all other candidates from these cells
                    eliminations = [
                        (r, c, v)
                        for (r, c) in cells_with_vals
                        for v in candidates[(r, c)]
                        if v not in val_set
                    ]
                    if eliminations:
                        return eliminations

def unique_rectangle_34(board):
    candidates = get_candidates(board)

    # Type 3: roof cells act as a pseudo-cell with their combined extra candidates.
    # Find enough companions in a shared unit to form a naked set, then eliminate.
    for r1 in range(9):
        for r2 in range(r1 + 1, 9):
            for c1 in range(9):
                for c2 in range(c1 + 1, 9):
                    if not ((r1 // 3 == r2 // 3) ^ (c1 // 3 == c2 // 3)):
                        continue

                    corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
                    cvals = {corner: candidates.get(corner, set()) for corner in corners}

                    for fi, fj in combinations(range(4), 2):
                        ri = [i for i in range(4) if i not in (fi, fj)]
                        fv = [cvals[corners[fi]], cvals[corners[fj]]]
                        rv = [cvals[corners[ri[0]]], cvals[corners[ri[1]]]]

                        if len(fv[0]) != 2 or fv[0] != fv[1]:
                            continue

                        pair = fv[0]
                        if not (pair.issubset(rv[0]) and pair.issubset(rv[1])):
                            continue

                        extra = (rv[0] - pair) | (rv[1] - pair)
                        if len(extra) < 2 or len(extra) > 3:
                            continue

                        roof = [corners[ri[0]], corners[ri[1]]]

                        for unit in shared_units(roof[0], roof[1]):
                            companions = [
                                cell for cell in unit
                                if cell not in roof
                                and cell in candidates
                                and candidates[cell].issubset(extra)
                            ]

                            needed = len(extra) - 1
                            if len(companions) < needed:
                                continue

                            for combo in combinations(companions, needed):
                                targets = [
                                    cell for cell in unit
                                    if cell not in roof and cell not in combo
                                ]
                                eliminations = [
                                    (r, c, v) for (r, c) in targets
                                    if (r, c) in candidates
                                    for v in extra
                                    if v in candidates[(r, c)]
                                ]
                                if eliminations:
                                    return eliminations

    # Type 4: one UR digit is locked to the roof cells in their shared unit,
    # so the other UR digit can be eliminated from both roof cells.
    for r1 in range(9):
        for r2 in range(r1 + 1, 9):
            for c1 in range(9):
                for c2 in range(c1 + 1, 9):
                    if not ((r1 // 3 == r2 // 3) ^ (c1 // 3 == c2 // 3)):
                        continue

                    corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
                    cvals = {corner: candidates.get(corner, set()) for corner in corners}

                    for fi, fj in combinations(range(4), 2):
                        ri = [i for i in range(4) if i not in (fi, fj)]
                        fv = [cvals[corners[fi]], cvals[corners[fj]]]
                        rv = [cvals[corners[ri[0]]], cvals[corners[ri[1]]]]

                        if len(fv[0]) != 2 or fv[0] != fv[1]:
                            continue

                        pair = fv[0]
                        if not (pair.issubset(rv[0]) and pair.issubset(rv[1])):
                            continue
                        if rv[0] == pair or rv[1] == pair:
                            continue

                        roof = [corners[ri[0]], corners[ri[1]]]

                        for unit in shared_units(roof[0], roof[1]):
                            for locked_val in pair:
                                other_val = next(v for v in pair if v != locked_val)

                                # locked_val must appear only in the roof cells within this unit
                                locked_elsewhere = any(
                                    cell not in roof
                                    and cell in candidates
                                    and locked_val in candidates[cell]
                                    for cell in unit
                                )
                                if locked_elsewhere:
                                    continue

                                eliminations = [
                                    (r, c, other_val)
                                    for (r, c) in roof
                                    if other_val in candidates.get((r, c), set())
                                ]
                                if eliminations:
                                    return eliminations

def xy_wing(board):
    candidates = get_candidates(board)
    bivalue = {cell: vals for cell, vals in candidates.items() if len(vals) == 2}

    for pivot, xy in bivalue.items():
        for wing1, xz in bivalue.items():
            if wing1 == pivot or not sees(pivot, wing1):
                continue
            shared1 = xy & xz
            if len(shared1) != 1:
                continue

            for wing2, yz in bivalue.items():
                if wing2 == pivot or wing2 == wing1 or not sees(pivot, wing2):
                    continue
                shared2 = xy & yz
                if len(shared2) != 1 or shared1 == shared2:
                    continue

                z_set = xz & yz
                if len(z_set) != 1 or next(iter(z_set)) in xy:
                    continue

                z = next(iter(z_set))
                eliminations = [
                    (r, c, z) for (r, c), vals in candidates.items()
                    if (r, c) not in (pivot, wing1, wing2)
                    and z in vals
                    and sees((r, c), wing1)
                    and sees((r, c), wing2)
                ]
                if eliminations:
                    return eliminations

def xyz_wing(board):
    candidates = get_candidates(board)
    bivalue = {cell: vals for cell, vals in candidates.items() if len(vals) == 2}

    for pivot, xyz in candidates.items():
        if len(xyz) != 3:
            continue

        # Wings must be bivalue, see the pivot, and be subsets of the pivot
        wings = [
            (cell, vals) for cell, vals in bivalue.items()
            if cell != pivot and sees(pivot, cell) and vals.issubset(xyz)
        ]

        for i in range(len(wings)):
            for j in range(i + 1, len(wings)):
                wing1, xz = wings[i]
                wing2, yz = wings[j]

                z_set = xz & yz
                if len(z_set) != 1:
                    continue
                if (xz | yz) != xyz:
                    continue

                z = next(iter(z_set))

                # Eliminate z from cells seeing all three: pivot, wing1, wing2
                eliminations = [
                    (r, c, z) for (r, c), vals in candidates.items()
                    if (r, c) not in (pivot, wing1, wing2)
                    and z in vals
                    and sees((r, c), pivot)
                    and sees((r, c), wing1)
                    and sees((r, c), wing2)
                ]
                if eliminations:
                    return eliminations

def bug_removal(board):
    candidates = get_candidates(board)
    unsolved = list(candidates.items())

    polyvalue = [(cell, vals) for cell, vals in unsolved if len(vals) > 2]
    if len(polyvalue) != 1:
        return None
    if not all(len(vals) == 2 for cell, vals in unsolved if cell != polyvalue[0][0]):
        return None

    (r, c), poly_vals = polyvalue[0]
    br, bc = (r // 3) * 3, (c // 3) * 3

    units = [
        [(r, c2) for c2 in range(9)],
        [(r2, c) for r2 in range(9)],
        [(br + i, bc + j) for i in range(3) for j in range(3)],
    ]

    for val in poly_vals:
        if all(
            sum(1 for cell in unit if val in candidates.get(cell, set())) % 2 == 1
            for unit in units
        ):
            return (r, c, val)

STRATEGIES = [
    ("Sudoku Basics",           naked_single),
    ("Hidden Single",           hidden_single),
    ("Intersections",           intersections),
    ("Forced Moves",            forced_moves),
    ("Pinned Squares",          pinned_squares),
    ("Locked Sets",             locked_sets),
    ("Intersection Removal",    intersection_removal),
    ("X-Wing",                  x_wing),
    ("Swordfish",               swordfish),
    ("Remote Pairs",            remote_pairs),
    ("Unique Rectangles (1&2)", unique_rectangle_12),
    ("Hidden Sets",             hidden_sets),
    ("Unique Rectangles (3&4)", unique_rectangle_34),
    ("XY-Wing",                 xy_wing),
    ("XYZ-Wing",                xyz_wing),
    ("BUG Removal",             bug_removal),
]
