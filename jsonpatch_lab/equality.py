"""
JSON equality (RFC 6902 §4.6).
"""

def json_equal(a, b) -> bool:
    """
    JSON value equality.
    - booleans compare only with booleans (blocks Python True == 1)
    - numbers compare numerically: 1 == 1.0
    - strings: exact
    - arrays: order + recurse
    - objects: key set + recurse, order irrelevant
    - null: both None
    """
    # bool check FIRST — blocks Python bool/int cross-equality
    a_is_bool = type(a) is bool
    b_is_bool = type(b) is bool
    if a_is_bool or b_is_bool:
        return a_is_bool and b_is_bool and a == b
    
    # numbers (int/float, not bool)
    a_is_num = isinstance(a, (int, float))
    b_is_num = isinstance(b, (int, float))
    if a_is_num and b_is_num:
        return float(a) == float(b)
    if a_is_num or b_is_num:
        return False
    
    # strings
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if isinstance(a, str) or isinstance(b, str):
        return False
    
    # null
    if a is None or b is None:
        return a is None and b is None
    
    # arrays
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, list) or isinstance(b, list):
        return False
    
    # objects
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(json_equal(a[k], b[k]) for k in a.keys())
    
    # fallback: type mismatch or unsupported
    return False
