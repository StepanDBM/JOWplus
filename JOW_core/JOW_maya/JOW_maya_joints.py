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
######################################################
# Multi-chain Divergence mode Helpers
######################################################

def get_joint_child_count(joint):
    return len(
        get_child_joints(joint)
    )


def is_branch_joint(joint):
    return get_joint_child_count(joint) > 1


def parent_has_multiple_joint_children(joint):
    parent = get_parent_joint(joint)

    if not parent:
        return False

    return is_branch_joint(parent)

def get_branch_aware_root_from_joint(joint):
    if not is_joint(joint):
        return None

    current = joint

    while True:
        parent = get_parent_joint(current)

        if not parent:
            return current

        if is_branch_joint(parent):
            return current

        current = parent

def get_unique_orient_roots_from_joints(joints, split_branches=False):
    roots = []

    for joint in joints or []:
        if not is_joint(joint):
            continue

        if split_branches:
            root = get_branch_aware_root_from_joint(joint)
        else:
            root = get_top_joint(joint)

        if not root:
            continue

        if root in roots:
            continue

        roots.append(root)

    return roots


def get_unique_orient_roots_from_selection(split_branches=False):
    joints = JOW_maya_selection.get_selected_joints(long=True)

    return get_unique_orient_roots_from_joints(joints, split_branches=split_branches)

def get_linear_chains_from_root(root):
    if not is_joint(root):
        return []

    chains = []

    def walk_chain(start_joint):
        chain = []
        current = start_joint

        while current:
            chain.append(current)

            children = get_child_joints(current)

            if not children:
                break

            if len(children) == 1:
                current = children[0]
                continue

            # Current joint is a branch point.
            # It belongs to this parent chain.
            # Each child starts a new independent chain.
            for child in children:
                child_chain = walk_chain(child)

                if len(child_chain) >= 2:
                    chains.append(child_chain)

            break

        return chain

    root_chain = walk_chain(root)

    if len(root_chain) >= 2:
        chains.insert(0, root_chain)

    return chains