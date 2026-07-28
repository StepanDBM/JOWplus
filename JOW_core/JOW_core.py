import maya.cmds as cmds
import JOW_core.JOW_math as JOW_math
from JOW_core.JOW_data import JointOrientation
from JOW_core.JOW_utils.JOW_undo import undo_chunk

@undo_chunk
def apply_orientation(settings):
    print("MODE =", settings.secondary_mode)
    if settings.roots:
        roots = settings.roots
    else:
        roots = get_unique_roots_from_selection()

    roots = [
        root for root in roots
        if cmds.objExists(root)
    ]

    if not roots:
        cmds.warning("Select one or more joints.")

        return

    if settings.primary_axis == settings.secondary_axis:
        cmds.warning("Primary Axis and Secondary Axis cannot be the same.")

        return

    if settings.custom_object is None:
        settings.custom_object = (get_custom_object_from_selection())

    for root in roots:
        orient_chain(
            root,
            settings
        )

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

        root = get_top_joint(jnt)

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
    child = get_first_child_joint(jnt)
    jnt_pos = JOW_math.get_world_pos(jnt)

    if child:
        child_pos = JOW_math.get_world_pos(child)
        return child_pos - jnt_pos

    if index > 0:
        prev_pos = JOW_math.get_world_pos(joints[index - 1])
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
    cmds.xform(
        temp,
        ws=True,
        matrix=matrix
    )

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
        if cmds.objExists(temp):
            cmds.delete(temp)

    restore_joint_positions(all_positions)

def compute_chain_orientation(root, settings):
    result = []
    joints = get_chain_joints(root)

    if len(joints) < 2:
        cmds.warning("{} has no child joints.".format(root))
        return result

    curve_plane_normal = JOW_math.compute_curve_plane_normal(
        joints,
        average_normals=settings.average_normals,
        flip_plane=settings.flip_plane
    )

    for i, jnt in enumerate(joints):
        child = get_first_child_joint(jnt)

        jnt_pos = JOW_math.get_world_pos(jnt)

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
    joints = get_chain_joints(root)
    position_data = store_joint_positions(joints)

    orientation_data = compute_chain_orientation(
        root,
        settings
    )

    apply_chain_orientation(
        orientation_data,
        position_data
    )

    restore_joint_positions(
        position_data
    )