# VERIFY.md — Clean-checkout verification

## Checkout

```
git clone https://github.com/necat101/python-json-patch-transaction-lab.git /tmp/jpt-verify
cd /tmp/jpt-verify
git checkout --detach 10412cee1405ecdd4415df8116525b3f9ade292e
git rev-parse HEAD
```

Output: `10412cee1405ecdd4415df8116525b3f9ade292e`

## Environment

- Python: `Python 3.12.3`
- OS: Linux 6.17.0-1009-aws x86_64
- Date: 2026-07-30

## Compile

```
python3 -m compileall jsonpatch_lab cases runner.py test_independent.py
```

Exit status: 0

## Runner

```
python3 runner.py
```

Output:
```
Cases: 33
  success: 15
  invalid_json: 2
  invalid_patch_document: 1
  invalid_operation: 5
  invalid_pointer: 1
  target_missing: 1
  source_missing: 2
  array_index_error: 2
  test_failed: 2
  move_into_descendant: 1
  root_removal_unsupported: 1
Passed: 33/33
```

Exit status: 0

## Independent unittests

```
python3 -m unittest test_independent -v
```

Output:
```
Ran 43 tests in 0.009s

OK
```

Exit status: 0

## Artifact comparison

Regenerated artifacts via `python3 runner.py` and compared byte-for-byte against committed versions:

| Artifact | Committed size | Regenerated size | Byte-identical | Notes |
|----------|---------------|------------------|----------------|-------|
| results.json | 21467 | 21467 | YES | exact match |
| results.csv | 6646 | 6644 | NO | Semantically identical. One field quoting difference: committed version quotes `root removal unsupported (lab policy)`; regenerated version omits quotes (correct per `csv.QUOTE_MINIMAL` since field contains no comma/quote/newline). CSV parses identically. |
| RESULTS.md | 2973 | 2973 | YES | exact match |

Diff for results.csv:
```diff
-...,RootRemovalUnsupported,"root removal unsupported (lab policy)",true
+...,RootRemovalUnsupported,root removal unsupported (lab policy),true
```

This is a CSV quoting variation only (QUOTE_MINIMAL behavior), content is identical.

## Git status

```
git status --short
 M results.csv
```

Only results.csv shows the quoting variation above. No other changes.

## Summary

- Case count: 33
- Classification totals: success 15, invalid_json 2, invalid_patch_document 1, invalid_operation 5, invalid_pointer 1, target_missing 1, source_missing 2, array_index_error 2, test_failed 2, move_into_descendant 1, root_removal_unsupported 1
- Runner: 33/33 PASS
- Independent unittests: 43/43 PASS
- Artifacts: results.json ✅ identical, RESULTS.md ✅ identical, results.csv ⚠️ semantically identical, 1 field quoting difference (QUOTE_MINIMAL)
- Python version: 3.12.3
- Wall time: ~2 seconds total (compile + runner + unittest)
- Failures: none
- Skips: none

Clean-checkout verification: **PASS**
