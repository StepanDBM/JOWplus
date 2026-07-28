# Joint Orient SDBM
import maya.cmds as cmds
import maya.api.OpenMaya as om

WINDOW_NAME = "jointOrientSDBM_UI"


# ------------------------------------------------------------
# Vector helpers
# ------------------------------------------------------------

def vec_from_pos(pos):
    return om.MVector(pos[0], pos[1], pos[2])


def get_world_pos(node):
    return vec_from_pos(
        cmds.xform(
            node,
            q=True,
            ws=True,
            t=True
        )
    )


def safe_normalize(v, fallback=om.MVector(0, 1, 0)):
    if v.length() < 0.0001:
        return fallback.normal()
    return v.normal()


def axis_index(axis):
    return {
        "X": 0,
        "Y": 1,
        "Z": 2
    }[axis]


def remaining_axis(primary_index, secondary_index):
    for i in [0, 1, 2]:
        if i != primary_index and i != secondary_index:
            return i


def is_cyclic_order(a, b, c):
    return (
        (a, b, c) == (0, 1, 2) or
        (a, b, c) == (1, 2, 0) or
        (a, b, c) == (2, 0, 1)
    )


def make_orientation_matrix(position, forward, up_reference, primary_axis, secondary_axis):
    """
    Builds a world matrix where:
    - selected primary axis points down the chain
    - selected secondary axis tries to follow the chosen secondary reference
    """

    primary_idx = axis_index(primary_axis)
    secondary_idx = axis_index(secondary_axis)

    if primary_idx == secondary_idx:
        raise RuntimeError(
            "Primary Axis and Secondary Axis cannot be the same."
        )

    third_idx = remaining_axis(
        primary_idx,
        secondary_idx
    )

    forward = safe_normalize(forward)

    up_reference = safe_normalize(up_reference)

    # Project secondary reference onto plane perpendicular to forward
    secondary = up_reference - (up_reference * forward) * forward

    if secondary.length() < 0.0001:

        fallback = om.MVector(0, 1, 0)

        if abs(forward * fallback) > 0.95:
            fallback = om.MVector(1, 0, 0)

        secondary = fallback - (fallback * forward) * forward

    secondary = safe_normalize(secondary)

    axes = [None, None, None]

    axes[primary_idx] = forward
    axes[secondary_idx] = secondary

    if is_cyclic_order(primary_idx, secondary_idx, third_idx):
        axes[third_idx] = axes[primary_idx] ^ axes[secondary_idx]
    else:
        axes[third_idx] = axes[secondary_idx] ^ axes[primary_idx]

    axes[third_idx] = safe_normalize(axes[third_idx])

    # Rebuild secondary to guarantee perfect orthogonality
    if is_cyclic_order(primary_idx, secondary_idx, third_idx):
        axes[secondary_idx] = axes[third_idx] ^ axes[primary_idx]
    else:
        axes[secondary_idx] = axes[primary_idx] ^ axes[third_idx]

    axes[secondary_idx] = safe_normalize(axes[secondary_idx])

    x = axes[0]
    y = axes[1]
    z = axes[2]

    return [
        x.x, x.y, x.z, 0,
        y.x, y.y, y.z, 0,
        z.x, z.y, z.z, 0,
        position.x, position.y, position.z, 1
    ]


# ------------------------------------------------------------
# Hierarchy helpers
# ------------------------------------------------------------

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


def get_custom_object_from_selection():
    selected = cmds.ls(sl=True, long=True) or []

    for obj in selected:

        if cmds.nodeType(obj) != "joint":
            return obj

    return None


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


# ------------------------------------------------------------
# Secondary modes
# ------------------------------------------------------------

def compute_curve_plane_normal(joints):
    """
    Computes an average normal from all consecutive joint triplets.
    No actual planes are created.
    """

    normals = []

    for i in range(1, len(joints) - 1):

        prev_pos = get_world_pos(joints[i - 1])
        curr_pos = get_world_pos(joints[i])
        next_pos = get_world_pos(joints[i + 1])

        a = curr_pos - prev_pos
        b = next_pos - curr_pos

        n = a ^ b

        if n.length() < 0.0001:
            continue

        n.normalize()

        if normals and (n * normals[0]) < 0:
            n *= -1

        normals.append(n)

    if not normals:
        return om.MVector(0, 1, 0)

    avg = om.MVector(0, 0, 0)

    for n in normals:
        avg += n

    if avg.length() < 0.0001:
        return om.MVector(0, 1, 0)

    return avg.normal()


def get_previous_mode_up(joints, index, fallback_normal):

    if index > 0 and index < len(joints) - 1:

        prev_pos = get_world_pos(joints[index - 1])
        curr_pos = get_world_pos(joints[index])
        next_pos = get_world_pos(joints[index + 1])

        a = curr_pos - prev_pos
        b = next_pos - curr_pos

        n = a ^ b

        if n.length() > 0.0001:
            return n.normal()

    return fallback_normal


def get_secondary_reference(
    mode,
    joints,
    index,
    curve_plane_normal,
    custom_object
):
    jnt = joints[index]
    jnt_pos = get_world_pos(jnt)

    if mode == "World":
        return om.MVector(0, 1, 0)

    elif mode == "Previous":
        return get_previous_mode_up(
            joints,
            index,
            curve_plane_normal
        )

    elif mode == "Curve Plane":
        return curve_plane_normal

    elif mode == "Custom Object":

        if not custom_object:
            cmds.warning(
                "Custom Object mode needs a non-joint object selected. Falling back to World mode."
            )
            return om.MVector(0, 1, 0)

        obj_pos = get_world_pos(custom_object)

        return obj_pos - jnt_pos

    return om.MVector(0, 1, 0)


# ------------------------------------------------------------
# Orientation application
# ------------------------------------------------------------

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


def orient_chain(root, primary_axis, secondary_axis, secondary_mode, custom_object):

    joints = get_chain_joints(root)

    if len(joints) < 2:

        cmds.warning(
            "{} has no child joints.".format(root)
        )

        return

    position_data = store_joint_positions(joints)

    curve_plane_normal = compute_curve_plane_normal(joints)

    for i, jnt in enumerate(joints):

        child = get_first_child_joint(jnt)

        if not child:
            continue

        jnt_pos = get_world_pos(jnt)
        child_pos = get_world_pos(child)

        forward = child_pos - jnt_pos

        if forward.length() < 0.0001:
            continue

        secondary_ref = get_secondary_reference(
            secondary_mode,
            joints,
            i,
            curve_plane_normal,
            custom_object
        )

        matrix = make_orientation_matrix(
            jnt_pos,
            forward,
            secondary_ref,
            primary_axis,
            secondary_axis
        )

        apply_world_orientation_to_joint(
            jnt,
            matrix,
            position_data
        )

    restore_joint_positions(position_data)


# ------------------------------------------------------------
# Main command
# ------------------------------------------------------------

def run_joint_orient_sdbm(*args):

    roots = get_unique_roots_from_selection()

    if not roots:

        cmds.warning(
            "Select one or more joints. The tool will process the root of each selected chain."
        )

        return

    primary_axis = cmds.optionMenu(
        primaryAxisMenu,
        q=True,
        v=True
    )

    secondary_axis = cmds.optionMenu(
        secondaryAxisMenu,
        q=True,
        v=True
    )

    if primary_axis == secondary_axis:

        cmds.warning(
            "Primary Axis and Secondary Axis cannot be the same."
        )

        return

    secondary_mode = cmds.optionMenu(
        secondaryModeMenu,
        q=True,
        v=True
    )

    custom_object = get_custom_object_from_selection()

    for root in roots:

        orient_chain(
            root,
            primary_axis,
            secondary_axis,
            secondary_mode,
            custom_object
        )

    print(
        "Joint Orient SDBM finished. Processed {} root chain(s).".format(
            len(roots)
        )
    )


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------

def build_joint_orient_sdbm_ui():

    global primaryAxisMenu
    global secondaryAxisMenu
    global secondaryModeMenu

    if cmds.window(
        WINDOW_NAME,
        exists=True
    ):
        cmds.deleteUI(WINDOW_NAME)

    cmds.window(
        WINDOW_NAME,
        title="Joint Orient SDBM",
        sizeable=False
    )

    cmds.columnLayout(
        adjustableColumn=True,
        rowSpacing=6
    )

    cmds.text(
        label="Primary Axis"
    )

    primaryAxisMenu = cmds.optionMenu()

    for axis in ["X", "Y", "Z"]:
        cmds.menuItem(label=axis)

    cmds.separator(h=8)

    cmds.text(
        label="Secondary Axis"
    )

    secondaryAxisMenu = cmds.optionMenu()

    for axis in ["X", "Y", "Z"]:
        cmds.menuItem(label=axis)

    cmds.optionMenu(
        secondaryAxisMenu,
        e=True,
        value="Y"
    )

    cmds.separator(h=8)

    cmds.text(
        label="Secondary Axis Mode"
    )

    secondaryModeMenu = cmds.optionMenu()

    for mode in [
        "World",
        "Previous",
        "Curve Plane",
        "Custom Object"
    ]:
        cmds.menuItem(label=mode)

    cmds.separator(h=10)

    cmds.button(
        label="Orient Selected Root Chain(s)",
        height=34,
        command=run_joint_orient_sdbm
    )

    cmds.showWindow()


build_joint_orient_sdbm_ui()