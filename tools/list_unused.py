"""
Generate a list of Python files that don't appear to be imported by other
project files using a simple heuristic. Writes results to
`tools/unused_candidates.txt`.

Usage:
    .venv/bin/python tools/list_unused.py

Notes:
- This is a conservative heuristic: it searches for import statements
  matching module paths and basenames. It can miss dynamic imports, CLI
  entrypoints, tests, and files referenced only by non-Python assets.
- Do NOT delete files automatically. Use `tools/prune_unused.py` to
  archive or delete after manual review.
"""

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {'.venv', '__pycache__', '.git', 'assets', 'third_party'}
OUT_FILE = ROOT / 'tools' / 'unused_candidates.txt'

def iter_py_files(root: Path):
    for p in root.rglob('*.py'):
        # skip files in excluded directories
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        yield p


def build_sources(py_files):
    sources = {}
    for p in py_files:
        try:
            sources[p] = p.read_text(encoding='utf-8')
        except Exception:
            sources[p] = ''
    return sources


def module_names_for_path(p: Path, root: Path):
    # convert path relative to repo root into dotted module path
    rel = p.relative_to(root).with_suffix('')
    return str(rel).replace(os.sep, '.')


def find_candidates():
    py_files = list(iter_py_files(ROOT))
    sources = build_sources(py_files)

    # compile simple import patterns
    # we'll search for 'import X' or 'from X import' where X is module path or basename
    imports_index = {p: False for p in py_files}

    for p in py_files:
        modname = module_names_for_path(p, ROOT)
        basename = p.stem

        patt_mod = re.compile(r"(^|\n)\s*(from|import)\s+" + re.escape(modname) + r"(\s|\.|$)")
        patt_base = re.compile(r"(^|\n)\s*(from|import)\s+" + re.escape(basename) + r"(\s|\.|$)")

        for other, text in sources.items():
            if other == p:
                continue
            if patt_mod.search(text) or patt_base.search(text):
                imports_index[p] = True
                break

    # filter out common entrypoint files we should not delete
    protected_names = {'setup', 'manage', 'wsgi', 'asgi', 'main', 'run', 'game', 'meun'}

    candidates = []
    for p, used in imports_index.items():
        if used:
            continue
        if p.stem in protected_names:
            continue
        # ignore package __init__
        if p.name == '__init__.py':
            continue
        candidates.append(p)

    candidates.sort()
    return candidates


def main():
    candidates = find_candidates()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open('w', encoding='utf-8') as f:
        for p in candidates:
            f.write(str(p.relative_to(ROOT)) + '\n')

    print(f"CANDIDATE_UNUSED_COUNT= {len(candidates)}")
    for p in candidates:
        print(p.relative_to(ROOT))
    print(f"Wrote list to {OUT_FILE}")

if __name__ == '__main__':
    main()
