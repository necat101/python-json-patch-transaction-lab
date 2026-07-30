"""
JSON Pointer (RFC 6901) decoding and resolution.
"""

from typing import Any


class PointerSyntaxError(Exception):
    pass


class PointerResolveError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def decode_pointer(pointer: str) -> list[str]:
    """
    Decode a JSON Pointer string into a list of reference tokens.
    RFC 6901 §3–4.

    - "" -> []
    - non-empty MUST start with "/"
    - validate escapes BEFORE decoding: every ~ must be followed by 0 or 1
    - decode ~1 -> / then ~0 -> ~
    - array index tokens are NOT validated here (done during resolution)
    """
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerSyntaxError("pointer must start with '/' or be empty")
    
    parts = pointer.split("/")[1:]  # drop leading ""
    tokens = []
    for raw_token in parts:
        # Validate escapes BEFORE decoding
        i = 0
        while i < len(raw_token):
            if raw_token[i] == "~":
                if i + 1 >= len(raw_token):
                    raise PointerSyntaxError(f"invalid escape: trailing ~ in token {raw_token!r}")
                nxt = raw_token[i + 1]
                if nxt not in ("0", "1"):
                    raise PointerSyntaxError(f"invalid escape ~{nxt} in token {raw_token!r}")
                i += 2
            else:
                i += 1
        # Decode: ~1 before ~0
        decoded = raw_token.replace("~1", "/").replace("~0", "~")
        tokens.append(decoded)
    return tokens


def _is_array_index_token(tok: str) -> bool:
    if tok == "0":
        return True
    if len(tok) >= 1 and tok[0] in "123456789":
        return all(c in "0123456789" for c in tok[1:])
    return False


def resolve_parent(doc: Any, tokens: list[str]) -> tuple[Any, str]:
    """
    Resolve all but the last token.
    Returns (parent_container, final_token).
    For root pointer (tokens=[]), parent is None, final_token = "".
    Raises PointerResolveError with code:
      target_missing, array_index_error
    """
    if not tokens:
        return None, ""
    
    cur = doc
    # resolve 0 .. n-2
    for i, tok in enumerate(tokens[:-1]):
        if isinstance(cur, dict):
            if tok in cur:
                cur = cur[tok]
            else:
                raise PointerResolveError("target_missing", f"missing object member {tok!r}")
        elif isinstance(cur, list):
            if tok == "-":
                raise PointerResolveError("array_index_error", " '-' not allowed in intermediate path")
            if not _is_array_index_token(tok):
                raise PointerSyntaxError(f"invalid array index token {tok!r}")
            idx = int(tok)
            if 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                raise PointerResolveError("array_index_error", f"array index {idx} out of range")
        else:
            # traversing into scalar
            raise PointerResolveError("target_missing", "intermediate target is scalar")
    
    return cur, tokens[-1]


def resolve(doc: Any, tokens: list[str]) -> Any:
    """Resolve full pointer. Raises PointerResolveError."""
    if not tokens:
        return doc
    parent, final_tok = resolve_parent(doc, tokens)
    if parent is None:
        return doc
    if isinstance(parent, dict):
        if final_tok in parent:
            return parent[final_tok]
        raise PointerResolveError("target_missing", f"missing member {final_tok!r}")
    elif isinstance(parent, list):
        if final_tok == "-":
            raise PointerResolveError("array_index_error", "'-' refers to nonexistent element")
        if not _is_array_index_token(final_tok):
            raise PointerSyntaxError(f"invalid array index {final_tok!r}")
        idx = int(final_tok)
        if 0 <= idx < len(parent):
            return parent[idx]
        raise PointerResolveError("array_index_error", f"array index {idx} out of range")
    else:
        raise PointerResolveError("target_missing", "parent is scalar")


def is_descendant(src_tokens: list[str], dest_tokens: list[str]) -> bool:
    """
    True if dest is a proper descendant of src.
    Token-wise, NOT string prefix.
    """
    if len(dest_tokens) <= len(src_tokens):
        return False
    return dest_tokens[:len(src_tokens)] == src_tokens


def get_value_at(doc: Any, tokens: list[str]) -> Any:
    """Resolve and return value, for copy/move source lookup."""
    return resolve(doc, tokens)
