"""Compatibility wrapper: re-export the third puzzle scene.

During this editing session the original `third_puzzle_scene_td.py` was
being rebuilt. Import the clean implementation added as
`third_puzzle_scene_td_clean.py` so demos keep working.
"""
from .third_puzzle_scene_td_clean import ThirdPuzzleScene  # type: ignore

__all__ = ["ThirdPuzzleScene"]
