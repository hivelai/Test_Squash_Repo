#!/usr/bin/env python3
"""Fixtures over 5 MB that make GitHub/GitLab remote blame fail (HV-145).

Blame cost grows with the number of lines, so each file is pretty-printed JSON
with ~14-byte lines, like big-data.json in hivelai/test-blame-large-file, which
fails with gateway_timeout at 17.5 MB / 1.25M lines.

Usage:
  python3 blame_timeout_gt5mb/gen_fixtures.py seed        # create all files
  python3 blame_timeout_gt5mb/gen_fixtures.py batch <n>   # rewrite 2000 scattered values per large file
  python3 blame_timeout_gt5mb/gen_fixtures.py small <n>   # rewrite lines in the small files
  python3 blame_timeout_gt5mb/gen_fixtures.py delete <n>  # delete 500 scattered records per large file
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MB = 1024 * 1024
LARGE_FILES = ["data_%02dmb.json" % n for n in (6, 8, 10, 12, 15, 18, 20, 25, 30, 40)]
SMALL_FILES = ["small_a.txt", "small_b.txt"]


def path(name):
    return os.path.join(HERE, name)


def target_size(name):
    return int(name[5:7]) * MB


def seed():
    for name in LARGE_FILES:
        rnd = random.Random(name)
        target = target_size(name)
        with open(path(name), "w") as f:
            f.write("[\n")
            size, i = 2, 0
            while size < target:
                rec = ' {\n  "id": %d,\n  "name": "item-%d",\n  "value": %.9f\n },\n' % (i, i, rnd.random())
                f.write(rec)
                size += len(rec)
                i += 1
            f.write(' {\n  "id": -1\n }\n]\n')
    for name in SMALL_FILES:
        with open(path(name), "w") as f:
            for i in range(50):
                f.write("%s line %d\n" % (name, i))


def batch(n):
    # Like the "update 2000 scattered values" commits that failed in QA.
    for name in LARGE_FILES:
        rnd = random.Random("%s-batch-%d" % (name, n))
        with open(path(name)) as f:
            lines = f.readlines()
        value_lines = [i for i, l in enumerate(lines) if l.startswith('  "value"')]
        for i in rnd.sample(value_lines, 2000):
            lines[i] = '  "value": %.9f\n' % rnd.random()
        with open(path(name), "w") as f:
            f.writelines(lines)


def small(n):
    for name in SMALL_FILES:
        with open(path(name)) as f:
            lines = f.readlines()
        for i in range(n % 5, len(lines), 5):
            lines[i] = "%s line %d edited in step %d\n" % (name, i, n)
        with open(path(name), "w") as f:
            f.writelines(lines)


def delete(n):
    # Pure deletions: drop 500 whole records (5 lines each) per large file.
    for name in LARGE_FILES:
        rnd = random.Random("%s-delete-%d" % (name, n))
        with open(path(name)) as f:
            lines = f.readlines()
        starts = [i for i in range(1, len(lines) - 4) if lines[i] == " {\n" and lines[i + 4] == " },\n"]
        drop = set()
        for s in rnd.sample(starts, 500):
            drop.update(range(s, s + 5))
        with open(path(name), "w") as f:
            f.writelines(l for i, l in enumerate(lines) if i not in drop)


if __name__ == "__main__":
    steps = {"batch": batch, "small": small, "delete": delete}
    if sys.argv[1:] == ["seed"]:
        seed()
    elif len(sys.argv) == 3 and sys.argv[1] in steps:
        steps[sys.argv[1]](int(sys.argv[2]))
    else:
        sys.exit(__doc__)
