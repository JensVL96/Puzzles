from config import *
from create_board import *
from display_board import *
from game_state import GameState
from ui import Button, Toggle

import pygame as pg

BX = 790  # button panel x
BW = 160  # button width
BH = 40   # button height
BS = 50   # button step


class Main():
    def __init__(self):
        self.run()

    def run(self):
        pg.init()
        self.screen = pg.display.set_mode(SCREEN_RES)
        pg.display.set_caption('Sudoku solver')

        created = create_board()
        state = GameState(created.board, created.solution)
        display = Display_board(self.screen)

        buttons = [
            Button((BX, 40,        BW, BH), "Check",           lambda: state.check()),
            Button((BX, 40+BS,     BW, BH), "Pencil",          lambda: state.pencil()),
            Button((BX, 40+BS*2,   BW, BH), "Undo",            lambda: state.undo()),
            Button((BX, 40+BS*3,   BW, BH), "Pinned",          lambda: state.pinned()),
            Button((BX, 40+BS*4,   BW, BH), "Answer",          lambda: state.answer()),
            Button((BX, 40+BS*5,   BW, BH), "Detailed Answer", lambda: state.detailed_answer()),
            Button((BX, 40+BS*6,   BW, BH), "Restart",         lambda: state.restart()),
            Button((BX, 40+BS*7,   BW, BH), "New",             lambda: state.new()),
        ]

        toggles = [
            Toggle((BX, 470, BW, 34), "Show Duplicates",  lambda v: setattr(state, 'show_duplicates', v)),
            Toggle((BX, 510, BW, 34), "Show Mistakes",    lambda v: setattr(state, 'show_mistakes', v)),
            Toggle((BX, 550, BW, 34), "Alt Highlights",   lambda v: setattr(state, 'alt_highlights', v)),
            Toggle((BX, 590, BW, 34), "Large Pencil",     lambda v: setattr(state, 'large_pencil', v)),
        ]

        toggles[0].active = state.show_duplicates  # on by default

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    exit()

                if event.type == pg.MOUSEBUTTONDOWN:
                    pos = pg.mouse.get_pos()
                    for btn in buttons:
                        btn.handle_click(pos)
                    for tog in toggles:
                        tog.handle_click(pos)
                    if state.input_lock != 1:
                        state.select(pos)

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_BACKSPACE:
                        state.erase()
                    elif state.input_lock != 1 and pg.K_1 <= event.key <= pg.K_9:
                        state.place(event.key - pg.K_0)

            self.screen.fill(BEIGE)

            cell = display.find_cell(state.selected_x, state.selected_y)
            display.draw(state.board)

            for btn in buttons:
                btn.draw(self.screen)
            for tog in toggles:
                tog.draw(self.screen)

            if state.blink and cell:
                state.alpha, state.a_change = display.blink(state.alpha, state.a_change)
                rect = pg.Rect(cell)
                surf = pg.Surface(rect.size, pg.SRCALPHA)
                surf.fill(state.blink_color)
                surf.set_alpha(state.alpha)
                self.screen.blit(surf, (rect.x, rect.y))

            if state.input_lock == 1:
                display.update(state.board, state.row_highlight, state.col_highlight, state.blk_highlight)

            pg.display.update()


if __name__ == '__main__':
    Main()
