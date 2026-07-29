import maya.cmds as cmds

from JOW_core.JOW_maya import JOW_maya_nodes

def get_selection(long=True):
    return cmds.ls(
        sl=True,
        long=long
    ) or []

def get_first_selected(long=True):
    selected = get_selection(long=long)

    if not selected:
        return None

    return selected[0]

def get_selected_joints(long=True):
    selected = get_selection(long=long)

    if not selected:
        return []

    return cmds.ls(
        selected,
        type="joint",
        long=long
    ) or []

def selection_has_joints():
    return bool(get_selected_joints(long=True))

def get_selected_non_joint(long=True):
    selected = get_selection(long=long)

    for node in selected:
        if not JOW_maya_nodes.exists(node):
            continue

        if JOW_maya_nodes.node_type(node) != "joint":
            return node

    return None

def get_selected_custom_object(long=True):
    return get_selected_non_joint(long=long)

def select_node(node, replace=True):
    if not JOW_maya_nodes.exists(node):
        return False

    cmds.select(node, r=replace)

    return True

def select_nodes(nodes, replace=True):
    existing_nodes = JOW_maya_nodes.unique_existing_nodes(nodes)

    if not existing_nodes:
        return False

    cmds.select(existing_nodes, r=replace)

    return True

def clear_selection():
    cmds.select(clear=True)