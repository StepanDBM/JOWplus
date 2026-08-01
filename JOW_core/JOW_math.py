import maya.api.OpenMaya as om
import maya.cmds as cmds
from JOW_core.JOW_maya import JOW_maya_transforms

def vec_from_pos(pos):
    return om.MVector(pos[0], pos[1], pos[2])


def get_world_pos(node):
    return vec_from_pos(JOW_maya_transforms.get_world_position(node))


def axis_index(axis):
    return {
        "X": 0,
        "Y": 1,
        "Z": 2
    }[axis]


def remaining_axis(primary, secondary):
    for i in [0, 1, 2]:
        if i != primary and i != secondary:
            return i

    raise RuntimeError("Could not resolve remaining axis.")

def is_cyclic_order(a, b, c):
    return (
        (a, b, c) == (0, 1, 2) or
        (a, b, c) == (1, 2, 0) or
        (a, b, c) == (2, 0, 1)
    )

def safe_normalize(v, fallback=om.MVector(0, 1, 0)):
    if v.length() < 0.0001:
        return fallback.normal()
    return v.normal()

def make_orientation_matrix(position, forward, secondary_reference, primary_axis, secondary_axis):
    """
    Builds a world matrix where:
    - selected primary axis points down the chain
    - selected secondary axis tries to follow the chosen secondary reference
    """

    primary_idx = axis_index(primary_axis)
    secondary_idx = axis_index(secondary_axis)

    if primary_idx == secondary_idx:
        raise RuntimeError("Primary Axis and Secondary Axis cannot be the same.")

    third_idx = remaining_axis(
        primary_idx,
        secondary_idx
    )

    forward = safe_normalize(forward)

    secondary_reference = safe_normalize(secondary_reference)

    # Project secondary reference onto plane perpendicular to forward
    secondary = secondary_reference - (secondary_reference * forward) * forward

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


def compute_curve_plane_normal(joints, average_normals=True, flip_plane=False):
    """
    Computes a normal from consecutive joint triplets.
    If average_normals is True, average all valid normals.
    If False, use the first valid normal.
    """

    normals = []

    for i in range(1, len(joints) - 1):
        prev_pos = JOW_maya_transforms.get_world_position(joints[i - 1])
        curr_pos = JOW_maya_transforms.get_world_position(joints[i])
        next_pos = JOW_maya_transforms.get_world_position(joints[i + 1])

        a = curr_pos - prev_pos
        b = next_pos - curr_pos

        n = a ^ b

        if n.length() < 0.0001:
            continue

        n.normalize()

        if normals and (n * normals[0]) < 0:
            n *= -1

        normals.append(n)

        if not average_normals:
            break

    if not normals:
        result = om.MVector(0, 1, 0)
    else:
        result = om.MVector(0, 0, 0)

        for n in normals:
            result += n

        if result.length() < 0.0001:
            result = om.MVector(0, 1, 0)
        else:
            result = result.normal()

    if flip_plane:
        result *= -1

    return result

def get_secondary_reference(
    mode,
    joints,
    index,
    curve_plane_normal,
    custom_object
):
    jnt = joints[index]
    jnt_pos = JOW_maya_transforms.get_world_position(jnt)

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
            #cmds.warning("Custom Object mode needs a non-joint object selected. Falling back to World mode.")
            return om.MVector(0, 1, 0)

        obj_pos = JOW_maya_transforms.get_world_position(custom_object)

        return obj_pos - jnt_pos

    return om.MVector(0, 1, 0)

def get_previous_mode_up(joints, index, fallback_normal):

    if index > 0 and index < len(joints) - 1:

        prev_pos = JOW_maya_transforms.get_world_position(joints[index - 1])
        curr_pos = JOW_maya_transforms.get_world_position(joints[index])
        next_pos = JOW_maya_transforms.get_world_position(joints[index + 1])

        a = curr_pos - prev_pos
        b = next_pos - curr_pos

        n = a ^ b

        if n.length() > 0.0001:
            return n.normal()

    return fallback_normal

def get_current_axis_from_matrix(matrix, axis):
    if not matrix:
        return None

    if axis == "X":
        return safe_normalize(
            vec_from_pos([
                matrix[0],
                matrix[1],
                matrix[2]
            ])
        )

    if axis == "Y":
        return safe_normalize(
            vec_from_pos([
                matrix[4],
                matrix[5],
                matrix[6]
            ])
        )

    if axis == "Z":
        return safe_normalize(
            vec_from_pos([
                matrix[8],
                matrix[9],
                matrix[10]
            ])
        )

    return None


def get_chain_current_axis_hint(joints, axis):
    result = om.MVector(0, 0, 0)
    reference = None

    for joint in joints or []:
        matrix = JOW_maya_transforms.get_world_matrix(
            joint
        )

        axis_vector = get_current_axis_from_matrix(
            matrix,
            axis
        )

        if axis_vector is None:
            continue

        if axis_vector.length() < 0.0001:
            continue

        axis_vector = axis_vector.normal()

        if reference is None:
            reference = axis_vector

        if axis_vector * reference < 0:
            axis_vector *= -1

        result += axis_vector

    if result.length() < 0.0001:
        return None

    return result.normal()


def compute_strongest_curve_plane_normal(joints, flip_plane=False):
    best_normal = None
    best_strength = 0.0

    for i in range(1, len(joints) - 1):
        prev_pos = JOW_maya_transforms.get_world_position(
            joints[i - 1]
        )

        curr_pos = JOW_maya_transforms.get_world_position(
            joints[i]
        )

        next_pos = JOW_maya_transforms.get_world_position(
            joints[i + 1]
        )

        if prev_pos is None or curr_pos is None or next_pos is None:
            continue

        a = curr_pos - prev_pos
        b = next_pos - curr_pos

        len_a = a.length()
        len_b = b.length()

        if len_a < 0.0001 or len_b < 0.0001:
            continue

        n = a ^ b
        cross_len = n.length()

        if cross_len < 0.0001:
            continue

        strength = cross_len / (len_a * len_b)

        if strength <= best_strength:
            continue

        best_strength = strength
        best_normal = n.normal()

    if best_normal is None:
        return None

    if flip_plane:
        best_normal *= -1

    return best_normal


def get_stabilized_curve_plane_normal(joints, settings):
    one_bone_normal = compute_one_bone_semantic_plane_normal(
        joints,
        flip_plane=settings.flip_plane
    )

    if one_bone_normal is not None:
        return one_bone_normal

    strongest_normal = compute_strongest_curve_plane_normal(
        joints,
        flip_plane=settings.flip_plane
    )

    if strongest_normal is not None:
        return strongest_normal

    axis_hint = get_chain_current_axis_hint(
        joints,
        settings.secondary_axis
    )

    if axis_hint is not None:
        if settings.flip_plane:
            axis_hint *= -1

        return axis_hint

    return compute_curve_plane_normal(
        joints,
        average_normals=settings.average_normals,
        flip_plane=settings.flip_plane
    )


def get_joint_children(joint):
    if not joint:
        return []

    if not cmds.objExists(joint):
        return []

    children = cmds.listRelatives(
        joint,
        children=True,
        type="joint",
        fullPath=True
    ) or []

    return children


def get_joint_world_position(joint):
    if not joint:
        return None

    if not cmds.objExists(joint):
        return None

    return JOW_maya_transforms.get_world_position(
        joint
    )


def get_distance_between_points(point_a, point_b):
    if point_a is None:
        return None

    if point_b is None:
        return None

    return (point_a - point_b).length()


def get_nearby_downstream_joint_for_tip(
    tip_joint,
    chain_joints,
    max_distance=8.0
):
    tip_position = get_joint_world_position(
        tip_joint
    )

    if tip_position is None:
        return None

    chain_lookup = set(
        chain_joints or []
    )

    all_joints = cmds.ls(
        type="joint",
        long=True
    ) or []

    best_joint = None
    best_child = None
    best_distance = None

    for candidate in all_joints:
        if candidate in chain_lookup:
            continue

        candidate_position = get_joint_world_position(
            candidate
        )

        if candidate_position is None:
            continue

        distance = get_distance_between_points(
            tip_position,
            candidate_position
        )

        if distance is None:
            continue

        if distance > max_distance:
            continue

        children = get_joint_children(
            candidate
        )

        if not children:
            continue

        child = children[0]

        if child in chain_lookup:
            continue

        child_position = get_joint_world_position(
            child
        )

        if child_position is None:
            continue

        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_joint = candidate
            best_child = child

    if best_joint is None:
        return None

    return best_joint, best_child


def compute_one_bone_semantic_plane_normal(
    joints,
    flip_plane=False
):
    if not joints:
        return None

    if len(joints) != 2:
        return None

    root_joint = joints[0]
    tip_joint = joints[1]

    root_position = get_joint_world_position(
        root_joint
    )

    tip_position = get_joint_world_position(
        tip_joint
    )

    if root_position is None:
        return None

    if tip_position is None:
        return None

    downstream = get_nearby_downstream_joint_for_tip(
        tip_joint,
        joints
    )

    if not downstream:
        return None

    downstream_joint, downstream_child = downstream

    downstream_child_position = get_joint_world_position(
        downstream_child
    )

    if downstream_child_position is None:
        return None

    a = tip_position - root_position
    b = downstream_child_position - tip_position

    if a.length() < 0.0001:
        return None

    if b.length() < 0.0001:
        return None

    normal = a ^ b

    if normal.length() < 0.0001:
        return None

    normal = normal.normal()

    if flip_plane:
        normal *= -1

    return normal