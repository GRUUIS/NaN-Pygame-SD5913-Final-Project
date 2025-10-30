"""
Entities Package - Game Objects and Components

This package contains all game entities including player, boss, bullets, platforms,
and the integrated boss battle scene. All components use globals.py for configuration.
"""

from .player import Player
from .boss import Perfectionist
from .bullets import Bullet, BulletManager
from .platform import Platform
from .boss_battle_scene import BossBattleScene

__all__ = [
    'Player',
    'Perfectionist', 
    'Bullet',
    'BulletManager',
    'Platform',
    'BossBattleScene'
]