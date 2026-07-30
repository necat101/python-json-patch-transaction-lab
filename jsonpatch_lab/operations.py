"""
JSON Patch operations (RFC 6902 §4.1–4.6).
"""

import copy
from . import pointer as ptr
from .equality import json_equal


class TestFailed(Exception):
    pass


class RootRemovalUnsupported(Exception):
    pass


class MoveIntoDescendant(Exception):
    pass


def _array_index_for_add(arr_len: int, tok: str) -> int:
    if tok == "-":
        return arr_len
    if not ptr._is_array_index_token(tok):
        raise ptr.PointerSyntaxError(f"invalid array index {tok!r}")
    idx = int(tok)
    if 0 <= idx <= arr_len:
        return idx
    raise ptr.PointerResolveError("array_index_error", f"add index {idx} out of range [0,{arr_len}]")


def _array_index_existing(arr_len: int, tok: str) -> int:
    if tok == "-":
        raise ptr.PointerResolveError("array_index_error", "'-' not allowed for existing target")
    if not ptr._is_array_index_token(tok):
        raise ptr.PointerSyntaxError(f"invalid array index {tok!r}")
    idx = int(tok)
    if 0 <= idx < arr_len:
        return idx
    raise ptr.PointerResolveError("array_index_error", f"index {idx} out of range [0,{arr_len-1}]")


def op_add_with_value(root, path_tokens, value):
    if not path_tokens:
        return value, True
    parent, final_tok = ptr.resolve_parent(root, path_tokens)
    if isinstance(parent, dict):
        parent[final_tok] = copy.deepcopy(value)
        return root, False
    elif isinstance(parent, list):
        idx = _array_index_for_add(len(parent), final_tok)
        parent.insert(idx, copy.deepcopy(value))
        return root, False
    else:
        raise ptr.PointerResolveError("target_missing", "add parent is scalar")


def op_remove(root, path_tokens):
    if not path_tokens:
        raise RootRemovalUnsupported("root removal unsupported (lab policy)")
    parent, final_tok = ptr.resolve_parent(root, path_tokens)
    if isinstance(parent, dict):
        if final_tok in parent:
            del parent[final_tok]
            return root, False
        raise ptr.PointerResolveError("target_missing", f"member {final_tok!r} missing")
    elif isinstance(parent, list):
        idx = _array_index_existing(len(parent), final_tok)
        del parent[idx]
        return root, False
    else:
        raise ptr.PointerResolveError("target_missing", "remove parent is scalar")


def op_replace_with_value(root, path_tokens, value):
    if not path_tokens:
        return value, True
    parent, final_tok = ptr.resolve_parent(root, path_tokens)
    if isinstance(parent, dict):
        if final_tok in parent:
            parent[final_tok] = copy.deepcopy(value)
            return root, False
        raise ptr.PointerResolveError("target_missing", f"member {final_tok!r} missing")
    elif isinstance(parent, list):
        idx = _array_index_existing(len(parent), final_tok)
        parent[idx] = copy.deepcopy(value)
        return root, False
    else:
        raise ptr.PointerResolveError("target_missing", "replace parent is scalar")


def op_test(root, path_tokens, value):
    actual = root if not path_tokens else ptr.resolve(root, path_tokens)
    if json_equal(actual, value):
        return root, False
    raise TestFailed("test failed")


def op_copy(root, from_tokens, path_tokens):
    try:
        src_val = ptr.get_value_at(root, from_tokens)
    except ptr.PointerResolveError as e:
        raise ptr.PointerResolveError("source_missing", str(e))
    src_copy = copy.deepcopy(src_val)
    if not path_tokens:
        return src_copy, True
    parent, final_tok = ptr.resolve_parent(root, path_tokens)
    if isinstance(parent, dict):
        parent[final_tok] = src_copy
        return root, False
    elif isinstance(parent, list):
        idx = _array_index_for_add(len(parent), final_tok)
        parent.insert(idx, src_copy)
        return root, False
    else:
        raise ptr.PointerResolveError("target_missing", "copy parent is scalar")


def op_move(root, from_tokens, path_tokens):
    # source lookup
    try:
        src_val = ptr.get_value_at(root, from_tokens)
    except ptr.PointerResolveError as e:
        raise ptr.PointerResolveError("source_missing", str(e))
    # descendant check
    if ptr.is_descendant(from_tokens, path_tokens):
        raise MoveIntoDescendant("move into own descendant")
    src_copy = copy.deepcopy(src_val)
    
    # root source?
    if not from_tokens:
        # moving root to root: no-op
        if not path_tokens:
            return src_copy, True
        # root -> descendant already rejected
        raise MoveIntoDescendant("move into own descendant")
    
    # remove source
    src_parent, src_final = ptr.resolve_parent(root, from_tokens)
    if isinstance(src_parent, dict):
        del src_parent[src_final]
    elif isinstance(src_parent, list):
        src_idx = _array_index_existing(len(src_parent), src_final)
        del src_parent[src_idx]
    else:
        raise ptr.PointerResolveError("source_missing", "source parent is scalar")
    
    # destination (post-removal)
    if not path_tokens:
        return src_copy, True
    
    dest_parent, dest_final = ptr.resolve_parent(root, path_tokens)
    if isinstance(dest_parent, dict):
        dest_parent[dest_final] = src_copy
        return root, False
    elif isinstance(dest_parent, list):
        idx = _array_index_for_add(len(dest_parent), dest_final)
        dest_parent.insert(idx, src_copy)
        return root, False
    else:
        raise ptr.PointerResolveError("target_missing", "move parent is scalar")


OPS = {
    "add": "add",
    "remove": "remove",
    "replace": "replace",
    "move": "move",
    "copy": "copy",
    "test": "test",
}
