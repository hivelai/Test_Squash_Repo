# Large-file blame timeout scenario (add-delete, merged PR)

Variant of `large_blame/` (see PR #33). GitHub GraphQL blame works up to ~705 KB and
times out from ~1.98 MB; today one failed file drops the whole commit and re-queues it
every hour forever.

## Commits
1. **seed** – adds ~680 KB, ~2 MB, ~5 MB JSON datasets and three small text files.
2. **add-delete** – **adds and deletes** lines in blame_fail_2mb.json, blame_fail_5mb.json and small_a/b/c.txt (rewrites some records, appends new ones).

## Expected after the fix
- Small files are blamed and classified (new work / rework).
- The two oversized files are skipped and recorded as blame-skipped.
- The commit is marked complete and is not re-queued on the next run.
