import maya.cmds as cmds

from JOW_core.JOW_maya import JOW_maya_nodes

def set_display_local_axis(node, state):
    if not JOW_maya_nodes.exists(node):
        return False
    attribute = "{}.displayLocalAxis".format(node)

    if not JOW_maya_nodes.attr_exists(attribute):
        return False

    try:
        cmds.setAttr(attribute, bool(state))

    except Exception:
        return False

    return True

def set_display_local_axis_for_nodes(nodes, state):
    changed_nodes = []

    for node in nodes or []:
        if not set_display_local_axis(node, state):
            continue

        changed_nodes.append(node)

    return changed_nodes

def refresh_scene():
    cmds.refresh()