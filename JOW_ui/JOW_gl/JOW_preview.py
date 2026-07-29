import JOW_core.JOW_math as JOW_math
from JOW_core import JOW_core
import maya.cmds as cmds

class PreviewJoint:
    def __init__(self):
        self.name = ""

        # Preview / proposed orientation.
        self.position = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.matrix = None

        # Current Maya orientation before Apply.
        self.current_position = None
        self.current_x_axis = None
        self.current_y_axis = None
        self.current_z_axis = None
        self.current_matrix = None

class PreviewChain:
    def __init__(self):
        self.root = None
        self.joints = []
        self.curve_plane_center = None
        self.curve_plane_normal = None
        self.previous_normals = []
        self.guide = None

class PreviewNormal:
    def __init__(self):
        self.position = None
        self.normal = None

class PreviewGuide:
    def __init__(self):
        self.name = None
        self.position = None



_CACHED_ROOTS = []
_CACHED_CUSTOM_OBJECT = None

_CACHE_LOCKED = False

def get_current_world_matrix(joint):
    return cmds.xform(
        joint,
        q=True,
        ws=True,
        matrix=True
    )

def get_cached_roots():
    roots, removed_count = validate_cached_roots()
    return roots

def validate_cache_and_get_removed_count():
    roots, removed_count = validate_cached_roots()
    return removed_count

def set_cache_locked(state):
    global _CACHE_LOCKED

    _CACHE_LOCKED = state


def is_cache_locked():
    return _CACHE_LOCKED


def get_cached_custom_object():
    custom_object, removed = validate_cached_custom_object()

    return custom_object

def get_invalid_cached_roots():
    invalid_roots = []

    for root in _CACHED_ROOTS:
        if not cmds.objExists(root):
            invalid_roots.append(root)

    return invalid_roots

def clear_cache():
    global _CACHED_ROOTS
    global _CACHED_CUSTOM_OBJECT

    _CACHED_ROOTS = []
    _CACHED_CUSTOM_OBJECT = None

def validate_cached_roots():
    global _CACHED_ROOTS

    valid_roots = []

    for root in _CACHED_ROOTS:
        if cmds.objExists(root):
            valid_roots.append(root)

    removed_count = len(_CACHED_ROOTS) - len(valid_roots)

    _CACHED_ROOTS = valid_roots

    return _CACHED_ROOTS[:], removed_count

def refresh_cache_from_selection():
    global _CACHED_ROOTS
    global _CACHED_CUSTOM_OBJECT

    roots = JOW_core.get_unique_roots_from_selection()

    if roots:
        _CACHED_ROOTS = roots[:]

    custom_object = JOW_core.get_custom_object_from_selection()

    if custom_object:
        _CACHED_CUSTOM_OBJECT = custom_object

    return _CACHED_ROOTS[:]

def clear_cached_roots():
    global _CACHED_ROOTS

    _CACHED_ROOTS = []

def validate_cached_custom_object():
    global _CACHED_CUSTOM_OBJECT

    if not _CACHED_CUSTOM_OBJECT:
        return None, False

    if cmds.objExists(_CACHED_CUSTOM_OBJECT):
        return _CACHED_CUSTOM_OBJECT, False

    _CACHED_CUSTOM_OBJECT = None

    return None, True


def clear_cached_custom_object():
    global _CACHED_CUSTOM_OBJECT

    _CACHED_CUSTOM_OBJECT = None


def update_cached_roots_from_selection():
    global _CACHED_ROOTS

    roots = JOW_core.get_unique_roots_from_selection()

    if roots:
        _CACHED_ROOTS = roots[:]

    return _CACHED_ROOTS[:]


def update_cached_custom_object_from_selection():
    global _CACHED_CUSTOM_OBJECT

    custom_object = JOW_core.get_custom_object_from_selection()

    if custom_object:
        _CACHED_CUSTOM_OBJECT = custom_object

    return _CACHED_CUSTOM_OBJECT


def get_preview_roots():
    if _CACHE_LOCKED:
        return get_cached_roots()

    roots = JOW_core.get_unique_roots_from_selection()

    if roots:
        global _CACHED_ROOTS
        _CACHED_ROOTS = roots[:]
        return roots

    return get_cached_roots()


def get_preview_custom_object(settings):
    global _CACHED_CUSTOM_OBJECT

    custom_object = JOW_core.get_custom_object_from_selection()

    if custom_object:
        _CACHED_CUSTOM_OBJECT = custom_object
        return custom_object

    if settings.custom_object:
        return settings.custom_object

    return _CACHED_CUSTOM_OBJECT

def set_cached_roots(roots):
    global _CACHED_ROOTS

    clean_roots = []

    for root in roots:
        if not root:
            continue

        if not cmds.objExists(root):
            continue

        if root not in clean_roots:
            clean_roots.append(root)

    _CACHED_ROOTS = clean_roots[:]

    return _CACHED_ROOTS[:]

def add_roots_to_cache(roots):
    global _CACHED_ROOTS

    validate_cached_roots()

    for root in roots:
        if not root:
            continue

        if not cmds.objExists(root):
            continue

        if root not in _CACHED_ROOTS:
            _CACHED_ROOTS.append(root)

    return _CACHED_ROOTS[:]

def remove_cached_root(root):
    global _CACHED_ROOTS

    if not root:
        return _CACHED_ROOTS[:]

    _CACHED_ROOTS = [
        cached_root for cached_root in _CACHED_ROOTS
        if cached_root != root
    ]

    return _CACHED_ROOTS[:]

def remove_cached_roots(roots):
    global _CACHED_ROOTS

    roots_to_remove = set(roots or [])

    _CACHED_ROOTS = [
        cached_root for cached_root in _CACHED_ROOTS
        if cached_root not in roots_to_remove
    ]

    return _CACHED_ROOTS[:]

def get_unique_roots_from_selection_for_cache():
    return JOW_core.get_unique_roots_from_selection()

def get_chain_center(joints):
    if not joints:
        return None

    center = JOW_math.vec_from_pos([0, 0, 0])

    for jnt in joints:
        center += JOW_math.get_world_pos(jnt)

    center /= len(joints)

    return center

def axes_from_matrix(matrix):
    x_axis = JOW_math.safe_normalize(
        JOW_math.vec_from_pos([
            matrix[0],
            matrix[1],
            matrix[2]
        ])
    )

    y_axis = JOW_math.safe_normalize(
        JOW_math.vec_from_pos([
            matrix[4],
            matrix[5],
            matrix[6]
        ])
    )

    z_axis = JOW_math.safe_normalize(
        JOW_math.vec_from_pos([
            matrix[8],
            matrix[9],
            matrix[10]
        ])
    )

    return x_axis, y_axis, z_axis


def position_from_matrix(matrix):
    return JOW_math.vec_from_pos([
        matrix[12],
        matrix[13],
        matrix[14]
    ])


def build_preview_chain(root, settings):
    preview_chain = PreviewChain()
    preview_chain.root = root

    joints = JOW_core.get_chain_joints(root)

    preview_chain.curve_plane_center = get_chain_center(joints)

    preview_chain.curve_plane_normal = JOW_math.compute_curve_plane_normal(
        joints,
        average_normals=settings.average_normals,
        flip_plane=settings.flip_plane
    )

    preview_chain.previous_normals = build_previous_normals(
        joints,
        preview_chain.curve_plane_normal
    )

    preview_chain.guide = build_preview_guide(settings)

    orientation_data = JOW_core.compute_chain_orientation(root, settings)
    for entry in orientation_data:
        preview_joint = PreviewJoint()
        preview_joint.name = entry.joint

        ##########################################################
        # Current Maya orientation before Apply
        ##########################################################
        current_matrix = get_current_world_matrix(
            entry.joint
        )

        preview_joint.current_matrix = current_matrix
        preview_joint.current_position = position_from_matrix(
            current_matrix
        )

        current_x_axis, current_y_axis, current_z_axis = axes_from_matrix(
            current_matrix
        )

        preview_joint.current_x_axis = current_x_axis
        preview_joint.current_y_axis = current_y_axis
        preview_joint.current_z_axis = current_z_axis

        ##########################################################
        # Preview / proposed JOW orientation
        ##########################################################
        preview_joint.matrix = entry.matrix
        preview_joint.position = position_from_matrix(
            entry.matrix
        )

        x_axis, y_axis, z_axis = axes_from_matrix(
            entry.matrix
        )

        preview_joint.x_axis = x_axis
        preview_joint.y_axis = y_axis
        preview_joint.z_axis = z_axis

        preview_chain.joints.append(
            preview_joint
        )

    return preview_chain


def build_preview_chains(settings):
    preview_chains = []

    roots = get_preview_roots()

    if not roots:
        return preview_chains

    if settings.custom_object is None:
        settings.custom_object = get_preview_custom_object(settings)

    for root in roots:
        preview_chain = build_preview_chain(root, settings)
        preview_chains.append(preview_chain)

    return preview_chains

def build_previous_normals(joints, curve_plane_normal):
    previous_normals = []

    for i in range(1, len(joints) - 1):
        normal = JOW_math.get_previous_mode_up(
            joints,
            i,
            curve_plane_normal
        )

        if not normal:
            continue

        preview_normal = PreviewNormal()
        preview_normal.position = JOW_math.get_world_pos(joints[i])
        preview_normal.normal = normal

        previous_normals.append(preview_normal)

    return previous_normals


def build_preview_guide(settings):
    if not settings.custom_object:
        return None

    if not cmds.objExists(settings.custom_object):
        return None

    guide = PreviewGuide()
    guide.name = settings.custom_object
    guide.position = JOW_math.get_world_pos(settings.custom_object)

    return guide