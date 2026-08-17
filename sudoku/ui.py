import pygame as pg
from config import *


class Button:
    def __init__(self, rect, label, callback):
        self.rect = pg.Rect(rect)
        self.label = label
        self.callback = callback
        self._font = None

    def draw(self, screen):
        if not self._font:
            self._font = pg.font.SysFont("comicsans", 24)
        pg.draw.rect(screen, WHITE, self.rect)
        pg.draw.rect(screen, BLACK, self.rect, 2)
        text = self._font.render(self.label, True, BLACK)
        screen.blit(text, text.get_rect(center=self.rect.center))

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()


class Toggle:
    def __init__(self, rect, label, callback):
        self.rect = pg.Rect(rect)
        self.label = label
        self.callback = callback
        self.active = False
        self._font = None

    def draw(self, screen):
        if not self._font:
            self._font = pg.font.SysFont("comicsans", 22)
        color = ACCENT if self.active else WHITE
        pg.draw.rect(screen, color, self.rect)
        pg.draw.rect(screen, BLACK, self.rect, 2)
        text = self._font.render(self.label, True, BLACK)
        screen.blit(text, text.get_rect(center=self.rect.center))

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.active = not self.active
            self.callback(self.active)
