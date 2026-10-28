#!/usr/bin/env python3
"""Deterministic fixtures for the large-file blame timeout scenario.

Usage:
  python3 large_blame_merged/gen_fixtures.py seed       # create the files
  python3 large_blame_merged/gen_fixtures.py mixed      # step 2: edit large + small files together
  python3 large_blame_merged/gen_fixtures.py large-only # step 3: edit only an oversized file
  python3 large_blame_merged/gen_fixtures.py control    # step 4: edit only files under the blame limit
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# GitHub GraphQL blame worked up to ~705 KB and failed from ~1.98 MB upwards.
LARGE_FILES = {
    "blame_ok_700kb.json": 680 * 1024,
    "blame_fail_2mb.json": 2 * 1024 * 1024,
    "blame_fail_5mb.json": 5 * 1024 * 1024,
}
SMALL_FILES = ["small_a.txt", "small_b.txt", "small_c.txt"]


def path(name):
    return os.path.join(HERE, name)


def record(i):
    # One JSON record per line so deletions show up as line-level changes in blame.
    return (
        '{"id": %d, "sku": "SKU-%08d", "name": "generated item %d", '
        '"price": %d.%02d, "tags": ["auto", "generated", "dataset"]},\n'
        % (i, i, i, i % 997, i % 100)
    )


def seed():
    for name, target in LARGE_FILES.items():
        with open(path(name), "w") as f:
            f.write("[\n")
            size, i = 2, 0
            while size < target:
                line = record(i)
                f.write(line)
                size += len(line)
                i += 1
            f.write('{"id": -1, "end": true}\n]\n')
    for name in SMALL_FILES:
        with open(path(name), "w") as f:
            for i in range(50):
                f.write("%s line %d\n" % (name, i))


def drop_lines(name, every, replace_with=None):
    """Delete every Nth record line (optionally replacing it) so the commit has deleted lines."""
    with open(path(name)) as f:
        lines = f.readlines()
    out = []
    for i, line in enumerate(lines):
        if 0 < i < len(lines) - 2 and i % every == 0:
            if replace_with is not None:
                out.append(replace_with % i)
            continue
        out.append(line)
    with open(path(name), "w") as f:
        f.writelines(out)


def mixed():
    drop_lines("blame_fail_2mb.json", 500, '{"id": %d, "edited": "mixed"},\n')
    drop_lines("blame_fail_5mb.json", 700)
    for name in SMALL_FILES:
        drop_lines(name, 5, name + " rewritten line %d\n")


def large_only():
    drop_lines("blame_fail_5mb.json", 300, '{"id": %d, "edited": "large-only"},\n')


def control():
    drop_lines("blame_ok_700kb.json", 400, '{"id": %d, "edited": "control"},\n')
    drop_lines("small_a.txt", 7)


if __name__ == "__main__":
    steps = {"seed": seed, "mixed": mixed, "large-only": large_only, "control": control}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        sys.exit(__doc__)
    steps[sys.argv[1]]()
