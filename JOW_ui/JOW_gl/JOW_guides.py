import maya.cmds as cmds

from JOW_core.JOW_utils.JOW_undo import undo_chunk


GUIDE_NAME = "JOW_Guide_LOC"


def guide_exists():
    return cmds.objExists(GUIDE_NAME)


def get_guide():
    if guide_exists():
        return GUIDE_NAME

    return None


@undo_chunk
def create_guide():
    if guide_exists():
        return GUIDE_NAME

    locator = cmds.spaceLocator(name=GUIDE_NAME)[0]

    return locator


def select_guide():
    guide = get_guide()

    if not guide:
        cmds.warning("No JOW guide locator exists.")
        return None

    cmds.select(guide, r=True)

    return guide


@undo_chunk
def delete_guide():
    guide = get_guide()

    if not guide:
        cmds.warning("No JOW guide locator exists.")
        return None

    cmds.delete(guide)

    return None


def get_selected_custom_object():
    selected = cmds.ls(sl=True, long=True) or []

    for obj in selected:
        if cmds.nodeType(obj) != "joint":
            return obj

    return None