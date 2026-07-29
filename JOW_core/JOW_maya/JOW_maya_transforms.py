import maya.cmds as cmds
import maya.api.OpenMaya as om

from JOW_core.JOW_maya import JOW_maya_nodes

def vector_from_position(position):
    return om.MVector(
        position[0],
        position[1],
        position[2]
    )

def get_world_position(node):
    if not JOW_maya_nodes.exists(node):
        return None

    position = cmds.xform(
        node,
        q=True,
        ws=True,
        t=True
    )

    return vector_from_position(position)

def get_world_matrix(node):
    if not JOW_maya_nodes.exists(node):
        return None

    return cmds.xform(
        node,
        q=True,
        ws=True,
        matrix=True
    )

def set_world_matrix(node, matrix):
    if not JOW_maya_nodes.exists(node):
        return False

    cmds.xform(
        node,
        ws=True,
        matrix=matrix
    )

    return True

def set_world_position(node, position):
    if not JOW_maya_nodes.exists(node):
        return False

    cmds.xform(
        node,
        ws=True,
        t=position
    )

    return True

def store_world_positions(nodes):
    data = {}

    for node in nodes or []:
        if not JOW_maya_nodes.exists(node):
            continue

        data[node] = cmds.xform(
            node,
            q=True,
            ws=True,
            t=True
        )

    return data

def restore_world_positions(position_data):
    for node, position in position_data.items():
        if not JOW_maya_nodes.exists(node):
            continue

        cmds.xform(
            node,
            ws=True,
            t=position
        )

def matrices_are_different(
    matrix_a,
    matrix_b,
    tolerance=0.00001
):
    if matrix_a is None or matrix_b is None:
        return True

    if len(matrix_a) != len(matrix_b):
        return True

    for a, b in zip(matrix_a, matrix_b):
        if abs(a - b) > tolerance:
            return True

    return False

def get_world_matrix_snapshot(nodes):
    snapshot = {}

    for node in nodes or []:
        if not JOW_maya_nodes.exists(node):
            continue

        try:
            matrix = get_world_matrix(node)

        except Exception:
            continue

        if matrix is None:
            continue

        snapshot[node] = matrix

    return snapshot

def snapshots_are_different(
    snapshot_a,
    snapshot_b,
    tolerance=0.00001
):
    if set(snapshot_a.keys()) != set(snapshot_b.keys()):
        return True

    for node in snapshot_a:
        matrix_a = snapshot_a.get(node)
        matrix_b = snapshot_b.get(node)

        if matrices_are_different(
            matrix_a,
            matrix_b,
            tolerance=tolerance
        ):
            return True
    return False