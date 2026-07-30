# python-json-patch-transaction-lab

A minimal, deterministic, standard-library-only Python lab that applies JSON Patch (RFC 6902) operations transactionally to an in-memory JSON document.

**Not a general-purpose JSON Patch library.** No HTTP server, no sockets, no network.

## Central question

Can a small implementation make the important abstraction boundaries observable:

- a patch document is an ordered program of operations, not a partial replacement object
- JSON Pointer resolution is separate from operation semantics
- object keys, array indexes, root pointer, `-`, `~0`, `~1` require different handling
- missing members ≠ members whose value is `null`
- `test` is a precondition; one failed operation prevents later commits
- `copy` must not create mutable aliases
- JSON equality must not inherit Python's `True == 1`
- parse errors, invalid patch structure, pointer failures, failed tests, and successful application are separate outcome categories

## Operations

All six RFC 6902 operations: `add`, `remove`, `replace`, `move`, `copy`, `test`.

## Source material — keep these categories separate

### 1. Hacker News opinions (non-normative)

HN thread 31301627 "What Is JSON Patch?" — https://news.ycombinator.com/item?id=31301627

Summary of opinions (not conclusions): JSON Patch described as "bizarre Frankenstein's monster", "verbose", "difficult to read", "not REST", "not sane RPC". Counterpoints: useful for multi-device sync, reduces complexity in practice, integrates with redux/undo-redo, successfully used in NHS Patient Demographic Service (FHIR). Complaints about `/` delimiter, `~0`/`~1` escaping, missing "create intermediate objects" mode, pointers-as-strings vs arrays, numeric keys vs array indexes ambiguity. Suggested alternatives: JSON Merge Patch (RFC 7386), custom RPC, event logs. **These opinions informed case selection but do not establish correctness.**

### 2. jsonpatch.com claims (non-normative)

https://jsonpatch.com/

Claims JSON Patch avoids sending whole documents, works with HTTP PATCH, operations applied in order, whole patch aborts on failure. Describes JSON Pointer escaping (`~0`, `~1`, `-` for array append). Lists libraries for many languages. **Informational only, not normative.**

### 3. Wikipedia summaries (non-normative)

- "JSON Patch" — web standard format for describing changes, media type `application/json-patch+json`, used with HTTP PATCH
- "PATCH (HTTP)" — request method for partial changes, PATCH document must be semantically well-defined, can have different media type than resource

**Wikipedia is not normative, do not cite as authoritative.**

### 4. Normative RFC 6902 / RFC 6901 requirements (controlling)

- **RFC 6902 JSON Patch** — patch document is array of operation objects, operations applied sequentially, evaluation stops on error, entire patch must not be deemed successful if any operation fails
- **RFC 6901 JSON Pointer** — `~1` → `/` then `~0` → `~`, empty pointer = root, array index ABNF, `-` = nonexistent end element
- **Operation semantics RFC 6902 §4.1–4.6**: `add` inserts/replaces, `remove` deletes, `replace` = remove+add, `move` = remove+add at new location, `copy` duplicates value, `test` compares with JSON equality
- **JSON equality RFC 6902 §4.6**: numerically equal numbers, same member sets for objects, order irrelevant, arrays ordered
- **Unrecognized members**: RFC 6902 §4 — "Members that are not explicitly defined … MUST be ignored"

These RFCs are the controlling source for implementation decisions.

### 5. Python documentation

- `json` — JSON parse/render, rejects non-finite numbers with default settings
- `copy.deepcopy` — deep copy for transaction isolation and copy operation

### 6. Local observations from this lab

33 fixed cases, 15 success / 18 failure across 10 error categories + root_removal_unsupported. Confirmed: pointer `~1`/`~0` decoding order matters, Python `True == 1` must be explicitly blocked for JSON equality, `copy.deepcopy` prevents source/destination aliasing, failed `test` rolls back entire patch, `null` vs missing are distinguishable in Python dicts, array insertion shifts correctly, move-into-descendant detection requires token-wise (not string-prefix) comparison, root removal is rejected as explicit lab policy (not RFC-mandated).

## Pointer rules

- Empty `""` = whole document
- Non-empty MUST start with `/`
- Validate escapes BEFORE decoding: every `~` must be `~0` or `~1`
- Decode `~1` → `/` then `~0` → `~`
- Object keys: Python `str` equality, no Unicode normalization
- Array index: `"0"` or `/[1-9][0-9]*/`
- `-` syntactically valid, operation acceptance is op-specific

## Root behavior

| op | path `""` | result |
|---|---|---|
| add | yes | whole-doc replace |
| replace | yes | whole-doc replace |
| test | yes | compare whole doc |
| remove | — | **REJECTED** `root_removal_unsupported` (lab policy, do NOT conflate absence with JSON null) |
| copy from | yes | copy entire doc |
| copy to | yes | replace entire doc |
| move from+to | yes+yes | no-op allowed |
| move from root to descendant | — | reject `move_into_descendant` |
| move to root | yes | source becomes new root |

## JSON equality

Booleans compare only with booleans (`True != 1`). Numbers compare numerically (`1 == 1.0`). Strings exact. Arrays ordered + recurse. Objects key-set + recurse, order irrelevant. Recurses into nested structures.

## Error taxonomy

`success`, `invalid_json`, `invalid_patch_document`, `invalid_operation`, `invalid_pointer`, `target_missing`, `source_missing`, `array_index_error`, `test_failed`, `move_into_descendant`, `root_removal_unsupported`

## Running

```bash
python3 runner.py              # 33 cases → results.json / results.csv / RESULTS.md
python3 -m unittest test_independent -v   # 43 independent tests
```

## Layout

```
jsonpatch_lab/pointer.py
jsonpatch_lab/equality.py
jsonpatch_lab/operations.py
jsonpatch_lab/apply.py
cases/manifest.py
runner.py
test_independent.py
```

## License

MIT
