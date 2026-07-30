#!/usr/bin/env python3
"""
Deterministic runner for python-json-patch-transaction-lab
"""

import json
import csv
import copy
from pathlib import Path

from jsonpatch_lab.apply import apply_patch
from jsonpatch_lab.equality import json_equal
from cases.manifest import CASES


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


OUTCOME_CODES = [
    "success",
    "invalid_json",
    "invalid_patch_document",
    "invalid_operation",
    "invalid_pointer",
    "target_missing",
    "source_missing",
    "array_index_error",
    "test_failed",
    "move_into_descendant",
    "root_removal_unsupported",
]


def run():
    rows = []
    for case in CASES:
        case_id = case["case_id"]
        # doc input
        if case.get("doc_input_kind") == "malformed":
            doc_input = case["doc_input_raw"]
            doc_obj = None
            doc_input_kind = "malformed"
            doc_input_raw = case["doc_input_raw"]
        else:
            doc_obj = copy.deepcopy(case.get("doc"))
            doc_input = doc_obj
            doc_input_kind = "json"
            doc_input_raw = None
        
        # patch input
        if case.get("patch_input_kind") == "malformed":
            patch_input = case["patch_input_raw"]
            patch_input_kind = "malformed"
            patch_input_raw = case["patch_input_raw"]
        else:
            patch_obj = case.get("patch")
            patch_input = patch_obj
            patch_input_kind = "json"
            patch_input_raw = None
        
        expected_outcome = case["expected_outcome"]
        expected_fail_index = case["expected_fail_index"]
        expected_result = case.get("expected_result")
        
        result = apply_patch(doc_input, patch_input)
        
        actual_outcome = result.outcome
        actual_fail_index = result.fail_index
        actual_result_doc = result.result_doc
        
        # doc_after
        doc_after = result.doc_after
        
        # check pass
        outcome_ok = (actual_outcome == expected_outcome)
        fail_index_ok = (actual_fail_index == expected_fail_index)
        
        result_ok = True
        if expected_outcome == "success":
            if actual_result_doc is None or expected_result is None:
                result_ok = False
            else:
                result_ok = json_equal(actual_result_doc, expected_result)
        
        # doc_after should equal original doc (for both success and failure)
        # For success, doc_after is snapshot before execution, not result
        doc_after_ok = True
        if doc_obj is not None:
            doc_after_ok = json_equal(doc_after, doc_obj)
        
        passed = outcome_ok and fail_index_ok and result_ok and doc_after_ok
        
        # post_mutate_check for copy_deep_isolation
        observation = result.observation or ""
        if case.get("post_mutate_check") and actual_outcome == "success" and actual_result_doc:
            # mutate copy
            try:
                if "dst" in actual_result_doc and isinstance(actual_result_doc["dst"], list):
                    actual_result_doc["dst"][0] = 99
                    src_ok = actual_result_doc.get("src") == [1, 2]
                    observation += f" post_mutate dst[0]=99, src_unchanged={src_ok}"
                    if not src_ok:
                        passed = False
            except Exception:
                pass
        
        row = {
            "case_id": case_id,
            "classification": expected_outcome,
            "doc_json": canonical(doc_obj) if doc_obj is not None else None,
            "doc_input_kind": doc_input_kind,
            "doc_input_raw": doc_input_raw,
            "patch_json": canonical(patch_obj) if patch_input_kind == "json" and 'patch_obj' in locals() else None,
            "patch_input_kind": patch_input_kind,
            "patch_input_raw": patch_input_raw,
            "expected_outcome": expected_outcome,
            "expected_fail_index": expected_fail_index,
            "expected_result_doc_json": canonical(expected_result) if expected_result is not None else None,
            "actual_outcome": actual_outcome,
            "actual_fail_index": actual_fail_index,
            "actual_result_doc_json": canonical(actual_result_doc) if actual_result_doc is not None else None,
            "doc_after_json": canonical(doc_after) if doc_after is not None else None,
            "exception_type": result.exception_type,
            "observation": observation,
            "pass": passed,
        }
        rows.append(row)
    
    # totals
    from collections import Counter
    counts = Counter(r["classification"] for r in rows)
    print(f"Cases: {len(rows)}")
    for code in OUTCOME_CODES:
        print(f"  {code}: {counts.get(code,0)}")
    passed_count = sum(1 for r in rows if r["pass"])
    print(f"Passed: {passed_count}/{len(rows)}")
    
    assert sum(counts.values()) == len(rows), "classification counts must sum to row count"
    
    # write results.json
    out_dir = Path(__file__).parent
    with open(out_dir / "results.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
        f.write("\n")
    
    # write results.csv
    fieldnames = [
        "case_id",
        "classification",
        "doc_json",
        "doc_input_kind",
        "doc_input_raw",
        "patch_json",
        "patch_input_kind",
        "patch_input_raw",
        "expected_outcome",
        "expected_fail_index",
        "expected_result_doc_json",
        "actual_outcome",
        "actual_fail_index",
        "actual_result_doc_json",
        "doc_after_json",
        "exception_type",
        "observation",
        "pass",
    ]
    with open(out_dir / "results.csv", "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        w.writerow(fieldnames)
        for r in rows:
            def fmt(v):
                if v is True: return "true"
                if v is False: return "false"
                if v is None: return ""
                return str(v)
            w.writerow([fmt(r.get(k)) if k in ("pass","expected_fail_index","actual_fail_index") else ("" if r.get(k) is None else r.get(k)) for k in fieldnames])
    
    # write RESULTS.md
    with open(out_dir / "RESULTS.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("# Results\n\n")
        f.write("| Case | Classification | Expected | Actual | Fail Idx | Pass |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['case_id']} | {r['classification']} | {r['expected_outcome']} | {r['actual_outcome']} | {r['actual_fail_index'] if r['actual_fail_index'] is not None else ''} | {'✓' if r['pass'] else '✗'} |\n")
        f.write("\n## Classification totals\n\n")
        f.write("| Classification | Count |\n|---|---|\n")
        for code in OUTCOME_CODES:
            f.write(f"| {code} | {counts.get(code,0)} |\n")
        f.write(f"\nTotal: {len(rows)} cases, {passed_count} passed.\n")
    
    return 0 if passed_count == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(run())
