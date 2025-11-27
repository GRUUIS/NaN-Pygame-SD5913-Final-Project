"""
Prune or archive files listed in `tools/unused_candidates.txt`.

Usage examples:
  Dry run (default):
    .venv/bin/python tools/prune_unused.py

  Archive candidates (move to `archive/unused/` preserving relative paths):
    .venv/bin/python tools/prune_unused.py --archive

  Delete permanently (be careful):
    .venv/bin/python tools/prune_unused.py --delete

  Interactive per-file prompt:
    .venv/bin/python tools/prune_unused.py --interactive --archive

The script is intentionally conservative: it requires the candidate list
file produced by `tools/list_unused.py` and defaults to dry-run.
"""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND_FILE = ROOT / 'tools' / 'unused_candidates.txt'
ARCHIVE_DIR = ROOT / 'archive' / 'unused'


def load_candidates():
    if not CAND_FILE.exists():
        print(f"Candidate file not found: {CAND_FILE}. Run tools/list_unused.py first.")
        return []
    lines = [l.strip() for l in CAND_FILE.read_text(encoding='utf-8').splitlines() if l.strip()]
    return [ROOT / l for l in lines]


def archive_file(p: Path):
    dest = ARCHIVE_DIR / p.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"ARCHIVE: {p} -> {dest}")
    shutil.move(str(p), str(dest))


def delete_file(p: Path):
    print(f"DELETE: {p}")
    p.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', action='store_true', help='Move candidates to archive/unused')
    parser.add_argument('--delete', action='store_true', help='Delete candidates permanently')
    parser.add_argument('--interactive', action='store_true', help='Ask before each action')
    parser.add_argument('--yes', action='store_true', help='Non-interactive approval for archive/delete')
    parser.add_argument('--main-file', help='Path (relative) to the main game file that must be typed to confirm destructive actions')
    args = parser.parse_args()

    candidates = load_candidates()
    if not candidates:
        return

    print(f"Found {len(candidates)} candidates from {CAND_FILE}")
    print("NOTE: This is a dry run unless --archive or --delete is specified.")
    # If performing destructive actions (archive/delete), require the user to
    # type the main game file path as an explicit confirmation to proceed.
    if args.archive or args.delete:
        expected = args.main_file if args.main_file else 'combine/game.py'
        try:
            typed = input(f"Type the main game file path to confirm (e.g. '{expected}'): ")
        except Exception:
            typed = ''
        if typed.strip() != expected:
            print('Confirmation failed: main file name did not match. Aborting.')
            return

    for p in candidates:
        if not p.exists():
            print(f"MISSING: {p} (skipping)")
            continue
        action = 'none'
        if args.archive:
            action = 'archive'
        elif args.delete:
            action = 'delete'
        else:
            action = 'report'

        if args.interactive and not args.yes:
            resp = input(f"[{action}] {p} ? (y/N) ")
            if resp.lower().strip() != 'y':
                print('skip')
                continue

        if action == 'report':
            print(f"DRY-RUN: {p}")
        elif action == 'archive':
            archive_file(p)
        elif action == 'delete':
            delete_file(p)

    print('Done')

if __name__ == '__main__':
    main()
