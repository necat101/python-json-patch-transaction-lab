#!/usr/bin/env python3
"""
Independent unittest suite — must NOT import cases.manifest, runner, or results.json
"""

import unittest
import copy
from jsonpatch_lab.apply import apply_patch
from jsonpatch_lab.equality import json_equal
from jsonpatch_lab import pointer as ptr


class TestJsonPatch(unittest.TestCase):
    
    def assertPatch(self, doc, patch, expected_outcome="success", expected_fail_index=None, expected_result=None):
        res = apply_patch(doc, patch)
        self.assertEqual(res.outcome, expected_outcome, msg=res.observation)
        self.assertEqual(res.fail_index, expected_fail_index)
        if expected_outcome == "success":
            self.assertTrue(json_equal(res.result_doc, expected_result),
                            f"got {res.result_doc}, expected {expected_result}")
        return res
    
    def test_add_member(self):
        self.assertPatch({"a": 1}, [{"op": "add", "path": "/b", "value": 2}],
                         expected_result={"a": 1, "b": 2})
    
    def test_replace_null(self):
        self.assertPatch({"x": None}, [{"op": "replace", "path": "/x", "value": "v"}],
                         expected_result={"x": "v"})
    
    def test_remove_keep_null(self):
        self.assertPatch({"a": 1, "n": None}, [{"op": "remove", "path": "/a"}],
                         expected_result={"n": None})
    
    def test_array_insert_mid(self):
        self.assertPatch({"arr": [0, 2, 3]}, [{"op": "add", "path": "/arr/1", "value": 1}],
                         expected_result={"arr": [0, 1, 2, 3]})
    
    def test_array_append_dash(self):
        self.assertPatch({"arr": [1]}, [{"op": "add", "path": "/arr/-", "value": 2}],
                         expected_result={"arr": [1, 2]})
    
    def test_dash_reject_replace(self):
        res = self.assertPatch({"arr": [1]}, [{"op": "replace", "path": "/arr/-", "value": 9}],
                               expected_outcome="array_index_error", expected_fail_index=0)
        self.assertTrue(json_equal(res.doc_after, {"arr": [1]}))
    
    def test_array_index_out_of_range(self):
        self.assertPatch({"arr": [1, 2]}, [{"op": "add", "path": "/arr/5", "value": 9}],
                         expected_outcome="array_index_error", expected_fail_index=0)
    
    def test_pointer_slash_escape(self):
        self.assertPatch({"a/b": 5}, [{"op": "replace", "path": "/a~1b", "value": 6}],
                         expected_result={"a/b": 6})
    
    def test_pointer_tilde_escape(self):
        self.assertPatch({"a~b": 5}, [{"op": "replace", "path": "/a~0b", "value": 6}],
                         expected_result={"a~b": 6})
    
    def test_invalid_pointer_escape(self):
        self.assertPatch({"a": 1}, [{"op": "replace", "path": "/a~2b", "value": 2}],
                         expected_outcome="invalid_pointer", expected_fail_index=0)
    
    def test_root_replace(self):
        self.assertPatch({"old": 1}, [{"op": "replace", "path": "", "value": {"new": 2}}],
                         expected_result={"new": 2})
    
    def test_root_add(self):
        self.assertPatch({"old": 1}, [{"op": "add", "path": "", "value": {"new": 3}}],
                         expected_result={"new": 3})
    
    def test_root_test_pass(self):
        self.assertPatch({"a": 1}, [{"op": "test", "path": "", "value": {"a": 1}}],
                         expected_result={"a": 1})
    
    def test_root_remove_rejected(self):
        self.assertPatch({"a": 1}, [{"op": "remove", "path": ""}],
                         expected_outcome="root_removal_unsupported", expected_fail_index=0)
    
    def test_copy_to_root(self):
        res = self.assertPatch({"x": 5, "y": {"z": 9}}, [{"op": "copy", "from": "/y", "path": ""}],
                               expected_result={"z": 9})
    
    def test_copy_from_root(self):
        res = self.assertPatch({"a": 1}, [{"op": "copy", "from": "", "path": "/b"}],
                               expected_result={"a": 1, "b": {"a": 1}})
    
    def test_move_to_root(self):
        self.assertPatch({"a": {"b": 2}}, [{"op": "move", "from": "/a/b", "path": ""}],
                         expected_result=2)
    
    def test_move_from_root_rejected(self):
        self.assertPatch({"a": {"b": 1}}, [{"op": "move", "from": "", "path": "/x"}],
                         expected_outcome="move_into_descendant", expected_fail_index=0)
    
    def test_copy_deep_isolation(self):
        res = apply_patch({"src": [1, 2], "dst": None}, [{"op": "copy", "from": "/src", "path": "/dst"}])
        self.assertEqual(res.outcome, "success")
        self.assertTrue(json_equal(res.result_doc, {"src": [1, 2], "dst": [1, 2]}))
        # mutate copy
        res.result_doc["dst"][0] = 99
        self.assertEqual(res.result_doc["src"], [1, 2], "source must not alias destination")
    
    def test_move_member(self):
        self.assertPatch({"a": 7, "b": None}, [{"op": "move", "from": "/a", "path": "/b"}],
                         expected_result={"b": 7})
    
    def test_move_into_descendant_rejected(self):
        self.assertPatch({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/b"}],
                         expected_outcome="move_into_descendant", expected_fail_index=0)
    
    def test_move_same_array_forward(self):
        # src_idx < dest_idx
        res = self.assertPatch({"arr": [0, 1, 2, 3]}, [{"op": "move", "from": "/arr/1", "path": "/arr/3"}],
                               expected_result={"arr": [0, 2, 3, 1]})
    
    def test_move_same_array_backward(self):
        res = self.assertPatch({"arr": [0, 1, 2, 3]}, [{"op": "move", "from": "/arr/3", "path": "/arr/1"}],
                               expected_result={"arr": [0, 3, 1, 2]})
    
    def test_move_source_missing(self):
        self.assertPatch({}, [{"op": "move", "from": "/missing", "path": "/x"}],
                         expected_outcome="source_missing", expected_fail_index=0)
    
    def test_copy_source_missing(self):
        self.assertPatch({}, [{"op": "copy", "from": "/missing", "path": "/x"}],
                         expected_outcome="source_missing", expected_fail_index=0)
    
    def test_test_pass(self):
        self.assertPatch({"k": "v"}, [{"op": "test", "path": "/k", "value": "v"}, {"op": "replace", "path": "/k", "value": "w"}],
                         expected_result={"k": "w"})
    
    def test_test_fail_rollback(self):
        doc = {"k": "v"}
        res = apply_patch(copy.deepcopy(doc), [{"op": "replace", "path": "/k", "value": "x"}, {"op": "test", "path": "/k", "value": "nope"}])
        self.assertEqual(res.outcome, "test_failed")
        self.assertEqual(res.fail_index, 1)
        self.assertTrue(json_equal(res.doc_after, doc), "original must be unchanged after failed test")
    
    def test_true_not_equal_1(self):
        self.assertPatch({"k": True}, [{"op": "test", "path": "/k", "value": 1}],
                         expected_outcome="test_failed", expected_fail_index=0)
    
    def test_number_equality_1_1_0(self):
        self.assertPatch({"n": 1.0}, [{"op": "test", "path": "/n", "value": 1}],
                         expected_result={"n": 1.0})
    
    def test_json_equality_nested(self):
        # bool vs int nested
        self.assertTrue(json_equal({"x": [True, 1]}, {"x": [True, 1.0]}))
        self.assertFalse(json_equal({"x": [True, 1]}, {"x": [1, 1]}))
        self.assertFalse(json_equal({"a": {"b": True}}, {"a": {"b": 1}}))
    
    def test_unknown_op(self):
        self.assertPatch({}, [{"op": "zap", "path": "/x"}],
                         expected_outcome="invalid_operation", expected_fail_index=0)
    
    def test_missing_op_member(self):
        self.assertPatch({}, [{"path": "/x", "value": 1}],
                         expected_outcome="invalid_operation", expected_fail_index=0)
    
    def test_missing_path_member(self):
        self.assertPatch({}, [{"op": "add", "value": 1}],
                         expected_outcome="invalid_operation", expected_fail_index=0)
    
    def test_op_not_string(self):
        self.assertPatch({}, [{"op": 123, "path": "/x", "value": 1}],
                         expected_outcome="invalid_operation", expected_fail_index=0)
    
    def test_path_not_string(self):
        self.assertPatch({}, [{"op": "add", "path": 123, "value": 1}],
                         expected_outcome="invalid_operation", expected_fail_index=0)
    
    def test_patch_not_array(self):
        res = apply_patch({}, {"op": "add", "path": "/x", "value": 1})
        self.assertEqual(res.outcome, "invalid_patch_document")
        self.assertIsNone(res.fail_index)
    
    def test_malformed_doc_json(self):
        res = apply_patch("{bad json", [{"op": "add", "path": "/x", "value": 1}])
        self.assertEqual(res.outcome, "invalid_json")
        self.assertEqual(res.input_kind, "doc")
    
    def test_malformed_patch_json(self):
        res = apply_patch({}, '[{"op":')
        self.assertEqual(res.outcome, "invalid_json")
        self.assertEqual(res.input_kind, "patch")
    
    def test_nonexistent_intermediate(self):
        self.assertPatch({}, [{"op": "add", "path": "/a/b", "value": 1}],
                         expected_outcome="target_missing", expected_fail_index=0)
    
    def test_ignored_extra_member(self):
        self.assertPatch({"k": 1}, [{"op": "replace", "path": "/k", "value": 2, "extra": "ignored"}],
                         expected_result={"k": 2})
    
    def test_error_precedence_unknown_op_beats_bad_pointer(self):
        # unknown op + invalid pointer -> must be invalid_operation
        res = apply_patch({}, [{"op": "zap", "path": "/a~2b", "value": 1}])
        self.assertEqual(res.outcome, "invalid_operation")
        self.assertEqual(res.fail_index, 0)
    
    def test_error_precedence_source_missing_beats_bad_dest(self):
        # source_missing must beat destination target_missing
        # (pointer syntax is validated before source resolution, so invalid_pointer WILL beat source_missing — that's correct per precedence §6)
        res = apply_patch({}, [{"op": "copy", "from": "/missing", "path": "/a/b"}])
        self.assertEqual(res.outcome, "source_missing")
    
    def test_error_codes_stable(self):
        codes_seen = set()
        tests = [
            ('{"bad', [], "invalid_json"),
            ({}, {"x": 1}, "invalid_patch_document"),
            ({}, [{"op": "x", "path": "/a"}], "invalid_operation"),
            ({"a": 1}, [{"op": "replace", "path": "/a~2", "value": 0}], "invalid_pointer"),
            ({}, [{"op": "add", "path": "/a/b", "value": 1}], "target_missing"),
            ({}, [{"op": "copy", "from": "/x", "path": "/y"}], "source_missing"),
            ({"arr": [1]}, [{"op": "replace", "path": "/arr/-", "value": 0}], "array_index_error"),
            ({"k": 1}, [{"op": "test", "path": "/k", "value": 2}], "test_failed"),
            ({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/b"}], "move_into_descendant"),
            ({"a": 1}, [{"op": "remove", "path": ""}], "root_removal_unsupported"),
        ]
        for doc, patch, expected_code in tests:
            res = apply_patch(doc if isinstance(doc, dict) else doc, patch if isinstance(patch, list) else patch)
            self.assertEqual(res.outcome, expected_code)
            codes_seen.add(res.outcome)
        for code in ["invalid_json", "invalid_patch_document", "invalid_operation", "invalid_pointer",
                     "target_missing", "source_missing", "array_index_error", "test_failed",
                     "move_into_descendant", "root_removal_unsupported"]:
            self.assertIn(code, codes_seen, f"code {code} not observed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
