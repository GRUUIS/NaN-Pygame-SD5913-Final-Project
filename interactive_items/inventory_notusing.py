# Copied from src/systems/inventory.py
"""Inventory system used by the map scene.

This provides a small in-game inventory with simple slot storage and a
toggleable UI. The drawing is intentionally lightweight but communicates
the state so it can be replaced by a richer UI later.
"""
import pygame
import os

class Inventory:
    def __init__(self, max_slots=8):
        self.max_slots = max_slots
        self.items = []
        self.visible = False
        self._icon_cache = {}

    def add_item(self, item):
        """Add an item (any Python object). Returns True on success."""
        if len(self.items) >= self.max_slots:
            return False
        try:
            item_id = None
            if isinstance(item, dict):
                item_id = item.get('id')
            elif hasattr(item, 'id'):
                item_id = getattr(item, 'id')
            if item_id and item_id not in self._icon_cache:
                candidates = [
                    os.path.join('assets', f"{item_id}.png"),
                    os.path.join('assets', 'sprites', 'items', f"{item_id}.png"),
                    os.path.join('assets', 'sprites', f"{item_id}.png"),
                ]
                from os import path
                found = None
                for p in candidates:
                    if path.exists(p):
                        found = p
                        break
                if not found and path.exists('assets'):
                    for root, dirs, files in os.walk('assets'):
                        for fn in files:
                            if fn.lower() == f"{item_id}.png":
                                found = os.path.join(root, fn)
                                break
                        if found:
                            break
                if found:
                    try:
                        surf = pygame.image.load(found).convert_alpha()
                        self._icon_cache[item_id] = surf
                    except Exception:
                        self._icon_cache[item_id] = None
        except Exception:
            pass
        self.items.append(item)
        return True

    def has_item(self, item_id: str) -> bool:
        """Return True if any item in inventory matches the given id."""
        for it in self.items:
            try:
                if isinstance(it, dict) and it.get('id') == item_id:
                    return True
                if hasattr(it, 'id') and getattr(it, 'id') == item_id:
                    return True
            except Exception:
                continue
        return False

    def toggle(self):
        self.visible = not self.visible
