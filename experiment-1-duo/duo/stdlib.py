"""
Duo Language — Standard Library
================================
Built-in functions available in every Duo program.

Originally assigned to agent_67691, but claude_e64e05 is writing the function
implementations proactively to unblock integration. agent_67691 should integrate
these into the interpreter's global environment.

Usage in interpreter:
    env = Environment()
    for name, func in get_builtins().items():
        env.define(name, func)
"""


class DuoRuntimeError(Exception):
    """Runtime error in Duo execution."""
    pass


class BuiltinFunction:
    """Wrapper for built-in functions so the interpreter can distinguish them."""
    def __init__(self, name, func, arity=None):
        self.name = name
        self.func = func
        self.arity = arity  # None means variadic

    def __call__(self, *args):
        if self.arity is not None and len(args) != self.arity:
            raise DuoRuntimeError(
                f"'{self.name}' expects {self.arity} argument(s), got {len(args)}")
        return self.func(*args)

    def __repr__(self):
        return f"<builtin {self.name}>"


def _duo_len(x):
    if isinstance(x, (list, str)):
        return float(len(x))
    raise DuoRuntimeError(f"'len' expects a list or string, got {type(x).__name__}")


def _duo_range(*args):
    if len(args) == 1:
        return list(range(int(args[0])))
    elif len(args) == 2:
        return list(range(int(args[0]), int(args[1])))
    elif len(args) == 3:
        return list(range(int(args[0]), int(args[1]), int(args[2])))
    raise DuoRuntimeError(f"'range' expects 1-3 arguments, got {len(args)}")


def _duo_type(x):
    if isinstance(x, float):
        return "number"
    elif isinstance(x, str):
        return "string"
    elif isinstance(x, bool):
        return "bool"
    elif isinstance(x, list):
        return "list"
    elif x is None:
        return "none"
    elif isinstance(x, BuiltinFunction):
        return "builtin"
    elif callable(x):
        return "function"
    return "unknown"


def _duo_str(x):
    if isinstance(x, float):
        if x == int(x):
            return str(int(x))
        return str(x)
    if isinstance(x, bool):
        return "true" if x else "false"
    if x is None:
        return "none"
    if isinstance(x, list):
        items = ", ".join(_duo_str(item) for item in x)
        return f"[{items}]"
    return str(x)


def _duo_num(x):
    if isinstance(x, float):
        return x
    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            raise DuoRuntimeError(f"Cannot convert '{x}' to number")
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    raise DuoRuntimeError(f"Cannot convert {type(x).__name__} to number")


def _duo_append(lst, val):
    if not isinstance(lst, list):
        raise DuoRuntimeError(f"'append' expects a list, got {type(lst).__name__}")
    return lst + [val]


def _duo_push(lst, val):
    """Alias for append."""
    return _duo_append(lst, val)


def _duo_pop(lst):
    if not isinstance(lst, list):
        raise DuoRuntimeError(f"'pop' expects a list, got {type(lst).__name__}")
    if not lst:
        raise DuoRuntimeError("'pop' called on empty list")
    return lst[:-1], lst[-1]  # returns (new_list, popped_value)


def _duo_head(lst):
    if not isinstance(lst, list):
        raise DuoRuntimeError(f"'head' expects a list, got {type(lst).__name__}")
    if not lst:
        raise DuoRuntimeError("'head' called on empty list")
    return lst[0]


def _duo_tail(lst):
    if not isinstance(lst, list):
        raise DuoRuntimeError(f"'tail' expects a list, got {type(lst).__name__}")
    if not lst:
        raise DuoRuntimeError("'tail' called on empty list")
    return lst[1:]


def _duo_map(lst, func):
    if not isinstance(lst, list):
        raise DuoRuntimeError(f"'map' expects a list as first argument")
    return [func(item) for item in lst]


def _duo_filter(lst, func):
    if not isinstance(lst, list):
        raise DuoRuntimeError(f"'filter' expects a list as first argument")
    return [item for item in lst if func(item)]


def _duo_reduce(lst, func, init):
    if not isinstance(lst, list):
        raise DuoRuntimeError(f"'reduce' expects a list as first argument")
    acc = init
    for item in lst:
        acc = func(acc, item)
    return acc


def _duo_abs(x):
    if not isinstance(x, (int, float)):
        raise DuoRuntimeError(f"'abs' expects a number, got {type(x).__name__}")
    return abs(x)


def _duo_min(*args):
    if len(args) == 1 and isinstance(args[0], list):
        return float(min(args[0]))
    return float(min(args))


def _duo_max(*args):
    if len(args) == 1 and isinstance(args[0], list):
        return float(max(args[0]))
    return float(max(args))


def _duo_input(prompt=""):
    return input(_duo_str(prompt) if prompt else "")


def _duo_int(x):
    """Truncate to integer (but still stored as float)."""
    return float(int(_duo_num(x)))


def _duo_split(s, sep=" "):
    if not isinstance(s, str):
        raise DuoRuntimeError(f"'split' expects a string, got {type(s).__name__}")
    return s.split(sep)


def _duo_join(lst, sep=""):
    if not isinstance(lst, list):
        raise DuoRuntimeError(f"'join' expects a list, got {type(lst).__name__}")
    return sep.join(_duo_str(item) for item in lst)


def get_builtins():
    """Return a dict of all built-in functions."""
    return {
        "len": BuiltinFunction("len", _duo_len, 1),
        "range": BuiltinFunction("range", _duo_range),
        "type": BuiltinFunction("type", _duo_type, 1),
        "str": BuiltinFunction("str", _duo_str, 1),
        "num": BuiltinFunction("num", _duo_num, 1),
        "int": BuiltinFunction("int", _duo_int, 1),
        "append": BuiltinFunction("append", _duo_append, 2),
        "push": BuiltinFunction("push", _duo_push, 2),
        "head": BuiltinFunction("head", _duo_head, 1),
        "tail": BuiltinFunction("tail", _duo_tail, 1),
        "abs": BuiltinFunction("abs", _duo_abs, 1),
        "min": BuiltinFunction("min", _duo_min),
        "max": BuiltinFunction("max", _duo_max),
        "input": BuiltinFunction("input", _duo_input),
        "split": BuiltinFunction("split", _duo_split),
        "join": BuiltinFunction("join", _duo_join),
    }
