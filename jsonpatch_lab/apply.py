"""
Apply a JSON Patch document transactionally.
"""

import json
import copy
from dataclasses import dataclass
from typing import Any

from . import pointer as ptr
from . import operations as ops


@dataclass
class PatchResult:
    outcome: str  # success | error_code
    fail_index: int | None
    result_doc: Any | None
    doc_after: Any
    exception_type: str | None
    observation: str
    input_kind: str | None  # "doc" | "patch" | None


def _canonical_json_str(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def apply_patch(doc_input, patch_input) -> PatchResult:
    """
    Apply patch transactionally.
    doc_input / patch_input: JSON string, or pre-parsed Python object.
    If string, JSON parse is attempted (invalid_json possible).
    """
    # Parse doc
    if isinstance(doc_input, str):
        try:
            doc = json.loads(doc_input)
        except Exception as e:
            return PatchResult(
                outcome="invalid_json",
                fail_index=None,
                result_doc=None,
                doc_after=None,
                exception_type=type(e).__name__,
                observation="doc parse failed",
                input_kind="doc",
            )
    else:
        doc = copy.deepcopy(doc_input)
    
    # Parse patch
    if isinstance(patch_input, str):
        try:
            patch = json.loads(patch_input)
        except Exception as e:
            return PatchResult(
                outcome="invalid_json",
                fail_index=None,
                result_doc=None,
                doc_after=copy.deepcopy(doc),
                exception_type=type(e).__name__,
                observation="patch parse failed",
                input_kind="patch",
            )
    else:
        patch = patch_input
    
    doc_before_snapshot = copy.deepcopy(doc)
    
    # Validate patch document type
    if not isinstance(patch, list):
        return PatchResult(
            outcome="invalid_patch_document",
            fail_index=None,
            result_doc=None,
            doc_after=copy.deepcopy(doc),
            exception_type=None,
            observation="patch is not an array",
            input_kind=None,
        )
    
    working = copy.deepcopy(doc)
    
    for i, op_obj in enumerate(patch):
        # 3. element type
        if not isinstance(op_obj, dict):
            return PatchResult(
                outcome="invalid_operation",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type=None,
                observation="element_not_object",
                input_kind=None,
            )
        
        # 4a. op member
        if "op" not in op_obj:
            return PatchResult(
                outcome="invalid_operation",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type=None,
                observation="missing_required_member:op",
                input_kind=None,
            )
        op_name = op_obj["op"]
        if not isinstance(op_name, str):
            return PatchResult(
                outcome="invalid_operation",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type=None,
                observation="wrong_type:op",
                input_kind=None,
            )
        # 4b. op value
        if op_name not in ops.OPS:
            return PatchResult(
                outcome="invalid_operation",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type=None,
                observation="unknown_op_name",
                input_kind=None,
            )
        
        # 4c. path member
        if "path" not in op_obj:
            return PatchResult(
                outcome="invalid_operation",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type=None,
                observation="missing_required_member:path",
                input_kind=None,
            )
        path_str = op_obj["path"]
        if not isinstance(path_str, str):
            return PatchResult(
                outcome="invalid_operation",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type=None,
                observation="wrong_type:path",
                input_kind=None,
            )
        
        # 4d/e. value / from validation
        has_value = "value" in op_obj
        if op_name in ("add", "replace", "test"):
            if not has_value:
                return PatchResult(
                    outcome="invalid_operation",
                    fail_index=i,
                    result_doc=None,
                    doc_after=copy.deepcopy(doc_before_snapshot),
                    exception_type=None,
                    observation="missing_required_member:value",
                    input_kind=None,
                )
        if op_name in ("move", "copy"):
            if "from" not in op_obj:
                return PatchResult(
                    outcome="invalid_operation",
                    fail_index=i,
                    result_doc=None,
                    doc_after=copy.deepcopy(doc_before_snapshot),
                    exception_type=None,
                    observation="missing_required_member:from",
                    input_kind=None,
                )
            from_str = op_obj["from"]
            if not isinstance(from_str, str):
                return PatchResult(
                    outcome="invalid_operation",
                    fail_index=i,
                    result_doc=None,
                    doc_after=copy.deepcopy(doc_before_snapshot),
                    exception_type=None,
                    observation="wrong_type:from",
                    input_kind=None,
                )
        
        # 5. pointer syntax
        try:
            path_tokens = ptr.decode_pointer(path_str)
        except ptr.PointerSyntaxError as e:
            return PatchResult(
                outcome="invalid_pointer",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type="PointerSyntaxError",
                observation=str(e),
                input_kind=None,
            )
        
        from_tokens = None
        if op_name in ("move", "copy"):
            try:
                from_tokens = ptr.decode_pointer(op_obj["from"])
            except ptr.PointerSyntaxError as e:
                return PatchResult(
                    outcome="invalid_pointer",
                    fail_index=i,
                    result_doc=None,
                    doc_after=copy.deepcopy(doc_before_snapshot),
                    exception_type="PointerSyntaxError",
                    observation="from: " + str(e),
                    input_kind=None,
                )
        
        # Execute operation
        try:
            if op_name == "add":
                new_root, is_root_repl = ops.op_add_with_value(working, path_tokens, op_obj["value"])
            elif op_name == "remove":
                new_root, is_root_repl = ops.op_remove(working, path_tokens)
            elif op_name == "replace":
                new_root, is_root_repl = ops.op_replace_with_value(working, path_tokens, op_obj["value"])
            elif op_name == "test":
                new_root, is_root_repl = ops.op_test(working, path_tokens, op_obj["value"])
            elif op_name == "copy":
                new_root, is_root_repl = ops.op_copy(working, from_tokens, path_tokens)
            elif op_name == "move":
                new_root, is_root_repl = ops.op_move(working, from_tokens, path_tokens)
            else:
                raise AssertionError("unreachable")
            
            if is_root_repl:
                working = new_root
            
        except ops.TestFailed as e:
            return PatchResult(
                outcome="test_failed",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type="TestFailed",
                observation=str(e),
                input_kind=None,
            )
        except ops.MoveIntoDescendant as e:
            return PatchResult(
                outcome="move_into_descendant",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type="MoveIntoDescendant",
                observation=str(e),
                input_kind=None,
            )
        except ops.RootRemovalUnsupported as e:
            return PatchResult(
                outcome="root_removal_unsupported",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type="RootRemovalUnsupported",
                observation=str(e),
                input_kind=None,
            )
        except ptr.PointerSyntaxError as e:
            return PatchResult(
                outcome="invalid_pointer",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type="PointerSyntaxError",
                observation=str(e),
                input_kind=None,
            )
        except ptr.PointerResolveError as e:
            # e.code is one of: target_missing, source_missing, array_index_error
            code = e.code if e.code in ("target_missing", "source_missing", "array_index_error") else "target_missing"
            return PatchResult(
                outcome=code,
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type="PointerResolveError",
                observation=str(e),
                input_kind=None,
            )
        except Exception as e:
            # unexpected
            return PatchResult(
                outcome="invalid_operation",
                fail_index=i,
                result_doc=None,
                doc_after=copy.deepcopy(doc_before_snapshot),
                exception_type=type(e).__name__,
                observation=f"unexpected: {e}",
                input_kind=None,
            )
    
    # success
    return PatchResult(
        outcome="success",
        fail_index=None,
        result_doc=copy.deepcopy(working),
        doc_after=copy.deepcopy(doc_before_snapshot),
        exception_type=None,
        observation="ok",
        input_kind=None,
    )
