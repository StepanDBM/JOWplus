import maya.cmds as cmds

from JOW_core.JOW_maya import JOW_maya_nodes
from JOW_core.JOW_maya import JOW_maya_selection


def is_joint(node):
    return JOW_maya_nodes.is_type(node, "joint")

def get_top_joint(joint):
    if not is_joint(joint):
        return None

    current = joint

    while True:
        parent = cmds.listRelatives(
            current,
            p=True,
            type="joint",
            fullPath=True
        )

        if not parent:
            break

        current = parent[0]

    return current

def get_child_joints(joint):
    if not is_joint(joint):
        return []

    return cmds.listRelatives(
        joint,
        c=True,
        type="joint",
        fullPath=True
    ) or []

def get_first_child_joint(joint):
    children = get_child_joints(joint)

    if not children:
        return None

    return children[0]

def get_parent_joint(joint):
    if not is_joint(joint):
        return None

    parent = cmds.listRelatives(
        joint,
        p=True,
        type="joint",
        fullPath=True
    ) or []

    if not parent:
        return None

    return parent[0]

def get_chain_joints(root):
    if not is_joint(root):
        return []

    joints = [root]

    descendants = cmds.listRelatives(
        root,
        ad=True,
        type="joint",
        fullPath=True
    ) or []

    descendants.reverse()

    joints.extend(descendants)

    return joints

def get_unique_roots_from_joints(joints):
    roots = []

    for joint in joints or []:
        if not is_joint(joint):
            continue

        root = get_top_joint(joint)

        if not root:
            continue

        if root in roots:
            continue

        roots.append(root)

    return roots

def get_unique_roots_from_selection():
    joints = JOW_maya_selection.get_selected_joints(long=True)
    return get_unique_roots_from_joints(joints)

def get_unique_joint_chains_from_roots(roots):
    nodes = []

    for root in roots or []:
        if not is_joint(root):
            continue

        joints = get_chain_joints(root)

        for joint in joints:
            if joint in nodes:
                continue

            nodes.append(joint)

    return nodes