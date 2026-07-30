import maya.cmds as cmds
import copy

from JOW_core.JOW_maya import JOW_maya_joints
from JOW_core.JOW_maya import JOW_maya_selection
from JOW_core.JOW_maya import JOW_maya_transforms
from JOW_core.JOW_maya import JOW_maya_nodes

import JOW_core.JOW_math as JOW_math
from JOW_core.JOW_data import JointOrientation
from JOW_core.JOW_utils.JOW_undo import undo_chunk

@undo_chunk
def apply_orientation(settings):
    print("MODE =", settings.secondary_mode)
    if settings.roots:
        roots = settings.roots
    else:
        roots = JOW_maya_joints.get_unique_roots_from_selection()
    roots = [
        root for root in roots
        if JOW_maya_nodes.exists(root)
    ]
    if not roots:
        cmds.warning("Select one or more joints.")
        return
    if settings.primary_axis == settings.secondary_axis:
        cmds.warning("Primary Axis and Secondary Axis cannot be the same.")
        return

    custom_objects_by_root = getattr(
        settings,
        "custom_objects_by_root",
        {}
    )

    applied_count = 0
    skipped_count = 0

    for root in roots:
        root_settings = copy.copy(settings)
        if settings.secondary_mode == "Custom Object":
            if root in custom_objects_by_root:
                root_settings.custom_object = custom_objects_by_root[root]
            elif settings.custom_object:
                root_settings.custom_object = settings.custom_object
            else:
                skipped_count += 1
                continue

        orient_chain(root, root_settings)
        applied_count += 1

    if applied_count == 0:
        cmds.warning(
            "No chains were oriented. Custom Object mode needs a guide for at least one target chain."
        )
        return

    if skipped_count:
        cmds.warning(
            "JOW orientation executed on {} chain(s). Skipped {} chain(s) without guide.".format(
                applied_count,
                skipped_count
            )
        )
    else:
        cmds.inViewMessage(
            amg="JOW orientation executed",
            pos="midCenter",
            fade=True
        )


def get_top_joint(jnt):
    current = jnt
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


def get_chain_joints(root):
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


def get_custom_object_from_selection():
    selected = cmds.ls(sl=True, long=True) or []

    for obj in selected:
        if cmds.nodeType(obj) != "joint":
            return obj

    return None

def get_unique_roots_from_selection():
    selected = cmds.ls(sl=True, long=True) or []

    joints = cmds.ls(
        selected,
        type="joint",
        long=True
    ) or []

    roots = []

    for jnt in joints:

        root = JOW_maya_joints.get_top_joint(jnt)

        if root not in roots:
            roots.append(root)

    return roots

def get_first_child_joint(jnt):
    children = cmds.listRelatives(
        jnt,
        c=True,
        type="joint",
        fullPath=True
    ) or []

    if not children:
        return None

    return children[0]

def get_parent_joint(jnt):
    parent = cmds.listRelatives(
        jnt,
        p=True,
        type="joint",
        fullPath=True
    ) or []

    if not parent:
        return None

    return parent[0]


def get_forward_for_joint(joints, index, jnt):
    child = JOW_maya_joints.get_first_child_joint(jnt)
    jnt_pos = JOW_maya_transforms.get_world_position(jnt)

    if child:
        child_pos = JOW_maya_transforms.get_world_position(child)
        return child_pos - jnt_pos

    if index > 0:
        prev_pos = JOW_maya_transforms.get_world_position(joints[index - 1])
        return jnt_pos - prev_pos

    return None


def store_joint_positions(joints):
    data = {}

    for jnt in joints:
        data[jnt] = cmds.xform(
            jnt,
            q=True,
            ws=True,
            t=True
        )

    return data


def restore_joint_positions(position_data):
    for jnt, pos in position_data.items():
        if cmds.objExists(jnt):
            cmds.xform(
                jnt,
                ws=True,
                t=pos
            )


def apply_world_orientation_to_joint(jnt, matrix, all_positions):
    temp = cmds.createNode(
        "transform",
        name="SDBM_orient_tmp"
    )
    JOW_maya_transforms.set_world_matrix(temp, matrix)
    try:
        cmds.delete(
            cmds.orientConstraint(
                temp,
                jnt,
                mo=False
            )
        )

        cmds.makeIdentity(
            jnt,
            apply=True,
            t=False,
            r=True,
            s=False,
            n=False
        )

    finally:
        if JOW_maya_nodes.exists(temp):
            cmds.delete(temp)

    JOW_maya_transforms.restore_world_positions(all_positions)

def compute_chain_orientation(root, settings):
    result = []
    joints = JOW_maya_joints.get_chain_joints(root)

    if len(joints) < 2:
        cmds.warning("{} has no child joints.".format(root))
        return result

    curve_plane_normal = JOW_math.compute_curve_plane_normal(
        joints,
        average_normals=settings.average_normals,
        flip_plane=settings.flip_plane
    )

    for i, jnt in enumerate(joints):
        is_end_joint = (i == len(joints) - 1)

        if is_end_joint and not settings.orient_end_joint:
            continue

        jnt_pos = JOW_maya_transforms.get_world_position(jnt)
        if jnt_pos is None:
            continue

        forward = get_forward_for_joint(
            joints,
            i,
            jnt
        )

        if forward is None:
            continue

        if forward.length() < 0.0001:
            continue

        secondary_ref = JOW_math.get_secondary_reference(
            settings.secondary_mode,
            joints,
            i,
            curve_plane_normal,
            settings.custom_object
        )

        matrix = JOW_math.make_orientation_matrix(
            jnt_pos,
            forward,
            secondary_ref,
            settings.primary_axis,
            settings.secondary_axis
        )

        result.append(
            JointOrientation(
                joint=jnt,
                matrix=matrix
            )
        )

    return result

def apply_chain_orientation(
    orientation_data,
    position_data
):
    for entry in orientation_data:
        apply_world_orientation_to_joint(
            entry.joint,
            entry.matrix,
            position_data
        )


def orient_chain(
    root,
    settings
):
    joints = JOW_maya_joints.get_chain_joints(root)
    position_data = JOW_maya_transforms.store_world_positions(joints)

    orientation_data = compute_chain_orientation(root, settings)
    apply_chain_orientation(orientation_data, position_data)
    JOW_maya_transforms.restore_world_positions(position_data)