import maya.cmds as cmds

from JOW_core.JOW_maya import JOW_maya_selection
from JOW_core.JOW_maya import JOW_maya_nodes
from JOW_core.JOW_maya import JOW_maya_transforms

from JOW_core.JOW_utils.JOW_undo import undo_chunk


GUIDE_PREFIX = "JOW_Guide_LOC"
SHARED_GUIDE_NAME = "JOW_Guide_LOC_SHARED"


def get_safe_node_token(node):
    if not node:
        return "Unknown"

    token = JOW_maya_nodes.short_name(node)
    clean = []

    for char in token:
        if char.isalnum() or char == "_":
            clean.append(char)
        else:
            clean.append("_")

    return "".join(clean)


def make_guide_name_for_root(root):
    return "{}_{}".format(
        GUIDE_PREFIX,
        get_safe_node_token(root)
    )


def is_jow_guide(node):
    if not node:
        return False

    short_name = JOW_maya_nodes.short_name(node)

    return (
        short_name == SHARED_GUIDE_NAME or
        short_name.startswith(GUIDE_PREFIX + "_")
    )


def get_all_guides():
    guides = cmds.ls(
        "{}*".format(GUIDE_PREFIX),
        type="transform",
        long=True
    ) or []

    result = []

    for guide in guides:
        if not is_jow_guide(guide):
            continue

        if guide in result:
            continue

        result.append(guide)

    return result


def get_selected_guides():
    selected = JOW_maya_selection.get_selection(long=True)
    guides = []

    for node in selected:
        if not is_jow_guide(node):
            continue

        if node in guides:
            continue

        guides.append(node)

    return guides


def create_guide_node(name, position=None):
    if JOW_maya_nodes.exists(name):
        guide = name
    else:
        guide = cmds.spaceLocator(name=name)[0]

    if position is not None:
        JOW_maya_transforms.set_world_position(
            guide,
            [
                position.x,
                position.y,
                position.z
            ]
        )

    return guide


@undo_chunk
def create_guide_for_root(root, position=None):
    guide_name = make_guide_name_for_root(root)

    return create_guide_node(
        guide_name,
        position=position
    )


@undo_chunk
def create_shared_guide(position=None):
    return create_guide_node(
        SHARED_GUIDE_NAME,
        position=position
    )


def select_guides(guides):
    valid_guides = []

    for guide in guides or []:
        if not JOW_maya_nodes.exists(guide):
            continue

        if guide in valid_guides:
            continue

        valid_guides.append(guide)

    if not valid_guides:
        cmds.warning("No JOW guide locator exists.")
        return []

    JOW_maya_selection.select_nodes(
        valid_guides,
        replace=True
    )

    return valid_guides


def select_all_guides():
    return select_guides(
        get_all_guides()
    )


@undo_chunk
def delete_guides(guides):
    deleted = []

    for guide in guides or []:
        if not JOW_maya_nodes.exists(guide):
            continue

        deleted.append(guide)

        cmds.delete(guide)

    return deleted


@undo_chunk
def delete_all_guides():
    return delete_guides(
        get_all_guides()
    )


def get_selected_custom_object():
    return JOW_maya_selection.get_selected_custom_object(long=True)
