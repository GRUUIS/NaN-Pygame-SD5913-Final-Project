# Copied from combine/meun.py
"""
Simple menu module for the `combine` runner.

This is a lightweight copy/adaptation of the project's main menu so the
`combine/game.py` file can show a menu on startup without depending on the
full `GameManager` class.
"""
import pygame
import os
import math
import random
from pathlib import Path
import sys
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
import globals as g
from src.utils.font import get_font, draw_text
from PIL import Image

class Meun:
    """A minimal menu that exposes `run()` which returns 'start' or 'quit'.
    """
    def __init__(self, screen):
        self.screen = screen
        repo_root = Path(__file__).resolve().parents[1]
        candidates = [
            repo_root / 'assets' / 'Silver.ttf',
            repo_root / 'assets' / 'silver.ttf',
            repo_root / 'assets' / 'Silver.TTF',
            repo_root / 'assets' / 'art' / 'Silver.ttf',
            repo_root / 'assets' / 'fonts' / 'Silver.ttf',
            repo_root / 'combine' / 'docs' / 'Silver.ttf',
        ]
        font_path = None
        for p in candidates:
            try:
                if p.exists():
                    font_path = str(p)
                    break
            except Exception:
                continue
        try:
            from src.utils.font import get_font_path
            self.font_path = get_font_path()
        except Exception:
            self.font_path = None
        if self.font_path:
            try:
                self.font_large = pygame.font.Font(self.font_path, 96)
                self.font_subtitle = pygame.font.Font(self.font_path, 28)
                self.font_medium = pygame.font.Font(self.font_path, 48)
                self.font_small = pygame.font.Font(self.font_path, 24)
                self.font_large_bold = pygame.font.Font(self.font_path, 96)
                self.font_large_bold.set_bold(True)
                self.font_subtitle_bold = pygame.font.Font(self.font_path, 28)
                self.font_subtitle_bold.set_bold(True)
                self.font_medium_bold = pygame.font.Font(self.font_path, 48)
                self.font_medium_bold.set_bold(True)
                self.font_small_bold = pygame.font.Font(self.font_path, 24)
                self.font_small_bold.set_bold(True)
            except Exception:
                self.font_large = get_font(96)
                self.font_subtitle = get_font(28)
                self.font_medium = get_font(48)
                self.font_small = get_font(24)
        else:
            self.font_large = get_font(96)
            self.font_subtitle = get_font(28)
            self.font_medium = get_font(48)
            self.font_small = get_font(24)
    # ...rest of the class remains unchanged...
