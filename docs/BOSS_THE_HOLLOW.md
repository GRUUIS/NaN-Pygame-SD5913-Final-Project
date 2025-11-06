# Boss 3: The Hollow (Nihilism)

Black humanoid silhouette that embodies emptiness. Retains the math-driven patterns from the previous Procrastinator boss but re-themed and streamlined.

## Player Experience

- Entry bubble: “You think words can scare me away?”
- Player primary attack in this fight: Voidfire (left mouse)
- Defeat bubble (shown above player): “This is not a threat-it's my process”
- Idle penalty: Standing still on ground escalates punishment (more/faster shards + optional HP drain)

## Patterns (FSM)

- Drift: Lissajous drift around a dynamic center influenced by stress/deadline
- Distraction Field: Poisson ring bullets around player
- Predictive Barrage: Quadratic interception lead + homing
- Log Spiral Burst: Angle-ramped spiral with exponential speed
- Void Shard Rain (Phase 3): Falling black squares, bias around player

## Tuning Knobs (globals.py)

- BOSS2_*: Reused tunables for movement and pattern intensities
- BULLET_SPEEDS: `void_shard`, `voidfire`
- BULLET_DAMAGE: `void_shard`, `voidfire`
- Idle Penalty:
  - `PLAYER_IDLE_THRESHOLD` (sec)
  - `PLAYER_IDLE_SHARD_INTERVAL` (sec)
  - `PLAYER_IDLE_HEALTH_DRAIN` (hp/sec)

## Visuals

- The Hollow drawn as a black rectangle body with subtle telegraph outline
- Voidfire: purple orb with faint aura
- Void Shards: solid black squares

## Notes

- Boss selection via CLI: `python main.py boss hollow` or `python main.py boss3`
- Left-click becomes Voidfire only in The Hollow battle; other bosses keep normal bullets
- Consider SFX and shader polish later (entry whoosh, shard impact, voidfire trail)
