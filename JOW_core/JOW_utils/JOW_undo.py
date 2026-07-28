import maya.cmds as cmds
from functools import wraps

_UNDO_DEPTH = 0

def undo_chunk(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _UNDO_DEPTH

        is_root = (_UNDO_DEPTH == 0)
        try:
            if is_root:
                cmds.undoInfo(openChunk=True)
            _UNDO_DEPTH += 1

            return func(*args, **kwargs)

        finally:
            _UNDO_DEPTH -= 1
            if is_root:
                cmds.undoInfo(closeChunk=True)

    return wrapper