"""Compatibility wrapper: re-export the top-down third puzzle scene.

This keeps code that imports `src.scenes.third_puzzle_scene.ThirdPuzzleScene`
working while the real implementation lives in `third_puzzle_scene_td.py`.
"""
from .third_puzzle_scene_td import ThirdPuzzleScene  # type: ignore

__all__ = ["ThirdPuzzleScene"]
