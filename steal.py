from __future__ import annotations

from types import FunctionType, ModuleType
from typing import Any, Callable, Literal


def steal(
    func: Callable,
    scope: ModuleType | dict[str, Any] | None = None,
    mode: Literal["strict", "modify", "replace"] = "modify",
) -> Callable:
    """Create a copy of a function, replace its global scope.

    The newly created function will act as if it was defined in the given
    global scope instead of its parent one. This is done by substituting the
    `__globals__` in the function copy.

    If `scope` is a module, a `__globals__` dictionary will be created based on
    the attributes of the module. If `scope` is a dictionary, it will be treated
    as the `__globals__` to use for the new function. If `scope` is not given,
    this returns a shallow copy of the given function.
    
    There are three possible modes of operation:.

    - `"strict"`: only the items from the function's parent scope are replaced.
      If any item is missing from the new scope, a `KeyError` will be raised.

    - `"modify"` (the default): the old scope is used. with items from `scope`
      replacing the old ones. Extra items not present in the original scope are
      added to the new one.

    - `"replace"`: replace the scopes as-is. No missing item checks are perfrmed.

    With `None` passed as a `scope`, the `mode` has no effect.

    To steal a function to the current module, pass `scope=globals()`.
    """
    if isinstance(scope, ModuleType):
        scope = dict(scope.__dict__)

    if scope is not None:
        if mode == "replace":
            pass  # Just use the new scope as is.
        elif mode == "modify":
            scope = dict(func.__globals__) | scope
        elif mode == "strict":
            scope = {key: scope[key] for key in func.__globals__.keys()}
        else:
            raise ValueError(f"Unknown mode: {mode}")
    else:
        scope = func.__globals__

    func_copy = FunctionType(
        func.__code__,
        scope,
        func.__name__,
        func.__defaults__,
        func.__closure__,
    )
    func_copy.__dict__.update(func.__dict__)
    return func_copy
