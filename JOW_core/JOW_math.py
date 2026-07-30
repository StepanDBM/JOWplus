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