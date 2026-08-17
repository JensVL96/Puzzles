import copy
from config import *
import solver


class GameState:
    def __init__(self, board, solution):
        self.board = board
        self.solution = solution
        self.initial = copy.deepcopy(board)
        self.history = []
        self.faults = []
        self.steps = []
        self.show_mistakes = False
        self.show_duplicates = True
        self.alt_highlights = False
        self.large_pencil = False
        self.selected_x = -1
        self.selected_y = -1
        self.blink = False
        self.alpha = 1
        self.a_change = True
        self.blink_color = GREEN
        self.input_lock = 0
        self.row_highlight = (-1, -1)
        self.col_highlight = (-1, -1)
        self.blk_highlight = (-1, -1)

    def _push_history(self):
        self.history.append(copy.deepcopy(self.board))

    def _clear_error(self):
        self.input_lock = 0
        self.row_highlight = (-1, -1)
        self.col_highlight = (-1, -1)
        self.blk_highlight = (-1, -1)
        self.blink_color = GREEN

    # --- Selection ---

    def select(self, mouse_pos):
        mx, my = mouse_pos
        x = next((i for i in range(9) if LINE_X[i] <= mx < LINE_X[i + 1]), -1)
        y = next((i for i in range(9) if LINE_Y[i] <= my < LINE_Y[i + 1]), -1)
        if x >= 0 and y >= 0:
            self.selected_x = x
            self.selected_y = y
            self.blink = True
        else:
            self.blink = False

    # --- Player input ---

    def place(self, val):
        x, y = self.selected_x, self.selected_y
        if x == -1 or val == 0:
            return
        if self.show_duplicates and not self._validate(val):
            return
        self._push_history()
        cell = self.board[x][y]
        if cell == 0:
            self.board[x][y] = val
        elif isinstance(cell, int):
            self.board[x][y] = [val]
        elif isinstance(cell, list) and val not in cell and len(cell) < 9:
            cell.append(val)

    def erase(self):
        x, y = self.selected_x, self.selected_y
        if x == -1:
            return
        self._push_history()
        self.board[x][y] = 0
        self._clear_error()

    def undo(self):
        if self.history:
            self.board = self.history.pop()
            self._clear_error()

    # --- Board actions ---

    def pencil(self):
        self._push_history()
        solver.pencil(self.board)

    def pinned(self):
        result = solver.pinned_squares(self.board)
        if result:
            row, col, val = result
            self._push_history()
            self.board[row][col] = val

    def hint(self):
        for _, strategy in solver.STRATEGIES:
            result = strategy(self.board)
            if result:
                self._push_history()
                if isinstance(result, tuple):
                    row, col, val = result
                    self.board[row][col] = val
                else:
                    for row, col, val in result:
                        if isinstance(self.board[row][col], list) and val in self.board[row][col]:
                            self.board[row][col].remove(val)
                return

    def answer(self):
        self._push_history()
        self.board = copy.deepcopy(self.solution)
        self._clear_error()

    def restart(self):
        self._push_history()
        self.board = copy.deepcopy(self.initial)
        self.faults = []
        self.steps = []
        self._clear_error()

    def new(self):
        from create_board import create_board
        created = create_board()
        self.board = created.board
        self.solution = created.solution
        self.initial = copy.deepcopy(created.board)
        self.history = []
        self.faults = []
        self.steps = []
        self.selected_x = -1
        self.selected_y = -1
        self.blink = False
        self._clear_error()

    # --- Checking ---

    def check(self):
        """Stores faults as (row, col) pairs. Empty list means no mistakes."""
        self.faults = []
        for r in range(9):
            for c in range(9):
                cell = self.board[r][c]
                if isinstance(cell, int) and cell != 0 and cell != self.solution[r][c]:
                    self.faults.append((r, c))
                elif isinstance(cell, list) and self.solution[r][c] not in cell:
                    self.faults.append((r, c))

    def detailed_answer(self):
        """Stores step-by-step solution as [(strategy_name, row, col, val), ...]."""
        self.steps = []
        board_copy = copy.deepcopy(self.board)
        while True:
            moved = False
            for name, strategy in solver.STRATEGIES:
                result = strategy(board_copy)
                if result:
                    if isinstance(result, tuple):
                        row, col, val = result
                        self.steps.append((name, row, col, val))
                        board_copy[row][col] = val
                    else:
                        for row, col, val in result:
                            self.steps.append((name, row, col, val))
                            if isinstance(board_copy[row][col], list) and val in board_copy[row][col]:
                                board_copy[row][col].remove(val)
                    moved = True
                    break
            if not moved:
                break

    # --- Validation ---

    def _validate(self, val):
        x, y = self.selected_x, self.selected_y
        row = col = blk = (-1, -1)
        found = False

        for i in range(9):
            if self.board[x][i] == val:
                col = (x, i)
                found = True
            if self.board[i][y] == val:
                row = (i, y)
                found = True

        ix, iy = x // 3, y // 3
        for i in range(ix * 3, ix * 3 + 3):
            for j in range(iy * 3, iy * 3 + 3):
                if self.board[i][j] == val:
                    blk = (i, j)
                    found = True

        if found:
            self.input_lock = 1
            self.row_highlight = row
            self.col_highlight = col
            self.blk_highlight = blk
            self.blink_color = RED
            return False
        return True
