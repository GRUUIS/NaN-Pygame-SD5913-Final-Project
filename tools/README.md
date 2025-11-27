Tools for detecting and pruning unused Python files

- `list_unused.py`: scans the repo and writes `tools/unused_candidates.txt`.
- `prune_unused.py`: conservative tool to archive or delete files listed in the candidates file.

Safety confirmation for destructive actions
- When using `prune_unused.py` with `--archive` or `--delete`, the script now
   requires you to type the main game file path (for example `combine/game.py`) as
   an explicit confirmation before it will perform any destructive action. You
   can also set the expected filename on the command line with `--main-file`.


Recommended workflow:
1. Run `tools/list_unused.py` and review `tools/unused_candidates.txt`.
2. If you'd like to archive them (reversible), run:
   `.venv/bin/python tools/prune_unused.py --archive`
3. If you are absolutely sure and want to permanently delete:
   `.venv/bin/python tools/prune_unused.py --delete`

Always keep a git commit before running destructive operations so you can revert.
