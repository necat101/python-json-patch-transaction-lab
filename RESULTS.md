# Results

| Case | Classification | Expected | Actual | Fail Idx | Pass |
|---|---|---|---|---|---|
| add_member | success | success | success |  | ✓ |
| replace_null | success | success | success |  | ✓ |
| remove_keep_null | success | success | success |  | ✓ |
| array_insert_mid | success | success | success |  | ✓ |
| array_append_dash | success | success | success |  | ✓ |
| pointer_slash_escape | success | success | success |  | ✓ |
| pointer_tilde_escape | success | success | success |  | ✓ |
| root_replace | success | success | success |  | ✓ |
| copy_deep_isolation | success | success | success |  | ✓ |
| move_member | success | success | success |  | ✓ |
| test_pass | success | success | success |  | ✓ |
| number_equality_1_1_0 | success | success | success |  | ✓ |
| ignored_extra_member | success | success | success |  | ✓ |
| root_add | success | success | success |  | ✓ |
| root_test_pass | success | success | success |  | ✓ |
| test_fail_rollback | test_failed | test_failed | test_failed | 1 | ✓ |
| true_not_equal_1 | test_failed | test_failed | test_failed | 0 | ✓ |
| dash_reject_replace | array_index_error | array_index_error | array_index_error | 0 | ✓ |
| array_index_out_of_range | array_index_error | array_index_error | array_index_error | 0 | ✓ |
| invalid_pointer_escape | invalid_pointer | invalid_pointer | invalid_pointer | 0 | ✓ |
| copy_source_missing | source_missing | source_missing | source_missing | 0 | ✓ |
| move_source_missing | source_missing | source_missing | source_missing | 0 | ✓ |
| move_into_descendant | move_into_descendant | move_into_descendant | move_into_descendant | 0 | ✓ |
| unknown_op | invalid_operation | invalid_operation | invalid_operation | 0 | ✓ |
| missing_op_member | invalid_operation | invalid_operation | invalid_operation | 0 | ✓ |
| missing_path_member | invalid_operation | invalid_operation | invalid_operation | 0 | ✓ |
| op_not_string | invalid_operation | invalid_operation | invalid_operation | 0 | ✓ |
| path_not_string | invalid_operation | invalid_operation | invalid_operation | 0 | ✓ |
| patch_not_array | invalid_patch_document | invalid_patch_document | invalid_patch_document |  | ✓ |
| malformed_doc_json | invalid_json | invalid_json | invalid_json |  | ✓ |
| malformed_patch_json | invalid_json | invalid_json | invalid_json |  | ✓ |
| nonexistent_intermediate | target_missing | target_missing | target_missing | 0 | ✓ |
| root_remove_rejected | root_removal_unsupported | root_removal_unsupported | root_removal_unsupported | 0 | ✓ |

## Classification totals

| Classification | Count |
|---|---|
| success | 15 |
| invalid_json | 2 |
| invalid_patch_document | 1 |
| invalid_operation | 5 |
| invalid_pointer | 1 |
| target_missing | 1 |
| source_missing | 2 |
| array_index_error | 2 |
| test_failed | 2 |
| move_into_descendant | 1 |
| root_removal_unsupported | 1 |

Total: 33 cases, 33 passed.
