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
    
    applied_count = 0
    skipped_count = 0

    for root in roots:
        if settings.secondary_mode == "Custom Object":
            oriented_count, root_skipped_count = orient_root_with_custom_object_mapping(
                root,
                settings
            )

            applied_count += oriented_count
            skipped_count += root_skipped_count
            continue

        root_settings = copy.copy(settings)
        oriented_count = orient_chain(root, root_settings)

        if oriented_count:
            applied_count += oriented_count

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

def get_position_lock_nodes_for_root(root):
    nodes = JOW_maya_joints.get_chain_joints(root)

    return [
        node for node in nodes
        if JOW_maya_nodes.exists(node)
    ]

def get_forward_for_joint(joints, index, jnt):
    jnt_pos = JOW_maya_transforms.get_world_position(jnt)
    if jnt_pos is None:
        return None

    if index + 1 < len(joints):
        next_pos = JOW_maya_transforms.get_world_position(joints[index + 1])
        if next_pos is None:
            return None
        return next_pos - jnt_pos

    if index > 0:
        prev_pos = JOW_maya_transforms.get_world_position(joints[index - 1])
        if prev_pos is None:
            return None
        return jnt_pos - prev_pos

    return None

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

def compute_linear_chain_orientation(joints, settings):
    result = []

    joints = [
        joint for joint in joints or []
        if JOW_maya_nodes.exists(joint)
    ]

    if len(joints) < 2:
        if joints:
            cmds.warning(
                "{} has no child joints.".format(
                    joints[0]
                )
            )

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

        forward = get_forward_for_joint(joints, i, jnt)

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

        result.append(JointOrientation(joint=jnt, matrix=matrix))

    return result

def compute_chain_orientation(root, settings):
    joints = JOW_maya_joints.get_chain_joints(root)
    return compute_linear_chain_orientation(joints, settings)

def orient_linear_chain(joints, settings, position_data=None):
    joints = [
        joint for joint in joints or []
        if JOW_maya_nodes.exists(joint)
    ]
    if len(joints) < 2:
        return False

    owns_position_data = (position_data is None)

    if owns_position_data:
        position_data = JOW_maya_transforms.store_world_positions(joints)
    orientation_data = compute_linear_chain_orientation(joints, settings)
    apply_chain_orientation(orientation_data, position_data)
    JOW_maya_transforms.restore_world_positions(position_data)

    return bool(orientation_data)

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


def orient_chain(root, settings):
    if getattr(settings, "split_branches", False):
        joint_chains = JOW_maya_joints.get_linear_chains_from_root(root)
    else:
        joint_chains = [JOW_maya_joints.get_chain_joints(root)]

    position_lock_nodes = get_position_lock_nodes_for_root(root)
    position_data = JOW_maya_transforms.store_world_positions(position_lock_nodes)
    oriented_count = 0

    for joints in joint_chains:
        if orient_linear_chain(
            joints,
            settings,
            position_data=position_data
        ):
            oriented_count += 1

        JOW_maya_transforms.restore_world_positions(position_data)
    return oriented_count

def orient_root_with_custom_object_mapping(root, settings):
    custom_objects_by_root = getattr(
        settings,
        "custom_objects_by_root",
        {}
    )

    if getattr(settings, "split_branches", False):
        joint_chains = JOW_maya_joints.get_linear_chains_from_root(root)
    else:
        joint_chains = [JOW_maya_joints.get_chain_joints(root)]

    guided_entries = []
    skipped_count = 0

    for joints in joint_chains:
        if not joints:
            continue

        orient_root = joints[0]
        custom_object = custom_objects_by_root.get(orient_root)

        if not custom_object:
            skipped_count += 1
            continue

        root_settings = copy.copy(settings)
        root_settings.custom_object = custom_object
        guided_entries.append((joints, root_settings))

    if not guided_entries:
        return 0, skipped_count

    lock_nodes = get_position_lock_nodes_for_root(root)

    target_nodes = set(
        joint
        for joints, root_settings in guided_entries
        for joint in joints
    )

    protected_nodes = [
        node for node in lock_nodes
        if node not in target_nodes
    ]

    position_data = JOW_maya_transforms.store_world_positions(lock_nodes)
    protected_matrix_data = JOW_maya_transforms.store_world_matrices(protected_nodes)

    oriented_count = 0

    for joints, root_settings in guided_entries:
        if orient_linear_chain(
            joints,
            root_settings,
            position_data=position_data
        ):
            oriented_count += 1

        JOW_maya_transforms.restore_world_matrices(protected_matrix_data)
        JOW_maya_transforms.restore_world_positions(position_data)

    return oriented_count, skipped_count