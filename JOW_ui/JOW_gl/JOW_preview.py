import copy

import maya.cmds as cmds

import JOW_core.JOW_math as JOW_math

from JOW_core import JOW_core

from JOW_core.JOW_maya import JOW_maya_nodes
from JOW_core.JOW_maya import JOW_maya_joints
from JOW_core.JOW_maya import JOW_maya_selection
from JOW_core.JOW_maya import JOW_maya_transforms


class PreviewJoint:
    def __init__(self):
        self.name = ""
        self.is_chain_root = False #chain-aware path addition

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

        self.root_parent = None    # Visual-only branch continuity link.
        self.root_parent_position = None

        self.bone_links = []


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
_CACHED_GUIDES_BY_ROOT = {}

_CACHE_LOCKED = False

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
        if not JOW_maya_nodes.exists(root):
            invalid_roots.append(root)

    return invalid_roots


def clear_cache():
    global _CACHED_ROOTS
    global _CACHED_CUSTOM_OBJECT
    global _CACHED_GUIDES_BY_ROOT

    _CACHED_ROOTS = []
    _CACHED_CUSTOM_OBJECT = None
    _CACHED_GUIDES_BY_ROOT = {}

def guide_owner_belongs_to_cached_roots(owner_root, cached_roots):
    if not owner_root:
        return False

    if not JOW_maya_nodes.exists(owner_root):
        return False

    for cached_root in cached_roots or []:
        if not cached_root:
            continue

        if not JOW_maya_nodes.exists(cached_root):
            continue

        if owner_root == cached_root:
            return True

        if owner_root.startswith(cached_root + "|"):
            return True

    return False

def get_duplicate_short_names(nodes):
    names_by_short_name = {}

    for node in nodes or []:
        short_name = JOW_maya_nodes.short_name(
            node
        )

        names_by_short_name.setdefault(
            short_name,
            []
        ).append(node)

    duplicates = {}

    for short_name, matching_nodes in names_by_short_name.items():
        if len(matching_nodes) <= 1:
            continue

        duplicates[short_name] = matching_nodes

    return duplicates


def validate_cached_roots():
    global _CACHED_ROOTS
    global _CACHED_GUIDES_BY_ROOT

    valid_roots = []

    for root in _CACHED_ROOTS:
        if JOW_maya_nodes.exists(root):
            valid_roots.append(root)

    removed_count = len(_CACHED_ROOTS) - len(valid_roots)

    _CACHED_ROOTS = valid_roots

    _CACHED_GUIDES_BY_ROOT = {
        root: guide
        for root, guide in _CACHED_GUIDES_BY_ROOT.items()
        if (
            guide_owner_belongs_to_cached_roots(
                root,
                _CACHED_ROOTS
            ) and
            JOW_maya_nodes.exists(guide)
        )
    }

    validate_cached_guides()

    return _CACHED_ROOTS[:], removed_count


def refresh_cache_from_selection():
    global _CACHED_ROOTS
    global _CACHED_CUSTOM_OBJECT

    roots = JOW_maya_joints.get_unique_roots_from_selection()

    if roots:
        _CACHED_ROOTS = roots[:]

    custom_object = JOW_maya_selection.get_selected_custom_object(long=True)

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

    if JOW_maya_nodes.exists(_CACHED_CUSTOM_OBJECT):
        return _CACHED_CUSTOM_OBJECT, False

    _CACHED_CUSTOM_OBJECT = None

    return None, True


def clear_cached_custom_object():
    global _CACHED_CUSTOM_OBJECT

    _CACHED_CUSTOM_OBJECT = None


def update_cached_roots_from_selection():
    global _CACHED_ROOTS
    roots = JOW_maya_joints.get_unique_roots_from_selection()
    if roots:
        _CACHED_ROOTS = roots[:]

    return _CACHED_ROOTS[:]


def update_cached_custom_object_from_selection():
    global _CACHED_CUSTOM_OBJECT
    custom_object = JOW_maya_selection.get_selected_custom_object(long=True)
    if custom_object:
        _CACHED_CUSTOM_OBJECT = custom_object

    return _CACHED_CUSTOM_OBJECT


def get_preview_roots():
    global _CACHED_ROOTS
    if _CACHE_LOCKED:
        return get_cached_roots()

    roots = JOW_maya_joints.get_unique_roots_from_selection()
    if roots:
        _CACHED_ROOTS = roots[:]
        return roots

    return get_cached_roots()


def get_preview_custom_object(settings):
    if settings.custom_object:
        return settings.custom_object

    return get_cached_custom_object()


def set_cached_roots(roots):
    global _CACHED_ROOTS
    clean_roots = []
    for root in roots or []:
        if not root:
            continue
        if not JOW_maya_nodes.exists(root):
            continue

        if root not in clean_roots:
            clean_roots.append(root)

    _CACHED_ROOTS = clean_roots[:]
    validate_cached_guides()

    return _CACHED_ROOTS[:]


def add_roots_to_cache(roots):
    global _CACHED_ROOTS
    validate_cached_roots()

    for root in roots or []:
        if not root:
            continue

        if not JOW_maya_nodes.exists(root):
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

    clear_cached_guide_for_root(root)

    return _CACHED_ROOTS[:]


def remove_cached_roots(roots):
    global _CACHED_ROOTS

    roots_to_remove = set(roots or [])

    _CACHED_ROOTS = [
        cached_root for cached_root in _CACHED_ROOTS
        if cached_root not in roots_to_remove
    ]

    for root in roots_to_remove:
        clear_cached_guide_for_root(root)

    return _CACHED_ROOTS[:]



def get_unique_roots_from_selection_for_cache():
    return JOW_maya_joints.get_unique_roots_from_selection()

def nodes_match(node_a, node_b):
    if not node_a or not node_b:
        return False

    if node_a == node_b:
        return True

    if not JOW_maya_nodes.exists(node_a):
        return False

    if not JOW_maya_nodes.exists(node_b):
        return False

    matches_a = cmds.ls(
        node_a,
        long=True
    ) or []

    matches_b = cmds.ls(
        node_b,
        long=True
    ) or []

    if not matches_a:
        return False

    if not matches_b:
        return False

    return matches_a[0] == matches_b[0]


def get_cached_guides_by_root():
    validate_cached_guides()

    return dict(_CACHED_GUIDES_BY_ROOT)


def get_cached_guide_for_root(root):
    validate_cached_guides()

    guide = _CACHED_GUIDES_BY_ROOT.get(root)

    if guide and JOW_maya_nodes.exists(guide):
        return guide

    return None


def root_has_cached_guide(root):
    return bool(
        get_cached_guide_for_root(root)
    )


def set_cached_guide_for_root(root, guide):
    global _CACHED_GUIDES_BY_ROOT
    global _CACHED_CUSTOM_OBJECT

    if not root:
        return

    if not guide:
        return

    if not JOW_maya_nodes.exists(root):
        return

    if not JOW_maya_nodes.exists(guide):
        return

    _CACHED_GUIDES_BY_ROOT[root] = guide

    if nodes_match(_CACHED_CUSTOM_OBJECT, guide):
        _CACHED_CUSTOM_OBJECT = None


def set_cached_custom_object(custom_object):
    global _CACHED_CUSTOM_OBJECT

    if not custom_object:
        return

    if not JOW_maya_nodes.exists(custom_object):
        return

    _CACHED_CUSTOM_OBJECT = custom_object


def clear_cached_guides():
    global _CACHED_GUIDES_BY_ROOT

    _CACHED_GUIDES_BY_ROOT = {}


def clear_cached_guide_for_root(root):
    global _CACHED_GUIDES_BY_ROOT

    if root in _CACHED_GUIDES_BY_ROOT:
        del _CACHED_GUIDES_BY_ROOT[root]


def clear_cached_guides_for_guides(guides):
    global _CACHED_GUIDES_BY_ROOT
    global _CACHED_CUSTOM_OBJECT

    guides = guides or []
    new_guides_by_root = {}

    for root, guide in _CACHED_GUIDES_BY_ROOT.items():
        remove_guide = False

        for deleted_guide in guides:
            if nodes_match(guide, deleted_guide):
                remove_guide = True
                break

        if remove_guide:
            continue

        new_guides_by_root[root] = guide

    _CACHED_GUIDES_BY_ROOT = new_guides_by_root

    for deleted_guide in guides:
        if nodes_match(_CACHED_CUSTOM_OBJECT, deleted_guide):
            _CACHED_CUSTOM_OBJECT = None
            break


def validate_cached_guides():
    global _CACHED_GUIDES_BY_ROOT

    valid_guides = {}

    cached_roots = [
        root for root in _CACHED_ROOTS
        if JOW_maya_nodes.exists(root)
    ]

    for root, guide in _CACHED_GUIDES_BY_ROOT.items():
        if not guide_owner_belongs_to_cached_roots(
            root,
            cached_roots
        ):
            continue

        if not JOW_maya_nodes.exists(guide):
            continue

        valid_guides[root] = guide

    _CACHED_GUIDES_BY_ROOT = valid_guides

    return dict(_CACHED_GUIDES_BY_ROOT)


def get_roots_without_per_root_guides(roots):
    result = []

    for root in roots or []:
        if root_has_cached_guide(root):
            continue

        result.append(root)

    return result


def get_effective_custom_object_for_root(root, fallback_custom_object=None):
    guide = get_cached_guide_for_root(root)

    if guide:
        return guide

    if fallback_custom_object and JOW_maya_nodes.exists(fallback_custom_object):
        return fallback_custom_object

    return get_cached_custom_object()


def get_custom_objects_by_root_for_roots(roots, fallback_custom_object=None):
    result = {}

    for root in roots or []:
        custom_object = get_effective_custom_object_for_root(
            root,
            fallback_custom_object=fallback_custom_object
        )

        if not custom_object:
            continue

        result[root] = custom_object

    return result

def preview_chains_have_guides(preview_chains):
    for chain in preview_chains or []:
        if not chain.guide:
            return False

        if not chain.guide.name:
            return False

    return bool(preview_chains)

def get_cached_guide_summary_text():
    validate_cached_guides()

    guide_names = []

    for guide in _CACHED_GUIDES_BY_ROOT.values():
        if not JOW_maya_nodes.exists(guide):
            continue

        short_name = JOW_maya_nodes.short_name(guide)

        if short_name in guide_names:
            continue

        guide_names.append(short_name)

    custom_object = get_cached_custom_object()

    if custom_object:
        short_name = JOW_maya_nodes.short_name(custom_object)

        if short_name not in guide_names:
            guide_names.append(short_name)

    if not guide_names:
        return "Guide: None"

    if len(guide_names) == 1:
        return "Guide: {}".format(guide_names[0])

    return "Guides: {}".format(len(guide_names))


def get_chain_center(joints):
    if not joints:
        return None

    center = JOW_math.vec_from_pos([0, 0, 0])
    valid_count = 0

    for joint in joints:
        position = JOW_maya_transforms.get_world_position(joint)

        if position is None:
            continue

        center += position
        valid_count += 1

    if valid_count == 0:
        return None

    center /= valid_count

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

def build_preview_chain_from_joints(joints, settings):
    if not joints:
        return None

    if len(joints) < 2:
        return None

    preview_chain = PreviewChain()
    preview_chain.root = joints[0]
    set_preview_chain_root_parent_link(
        preview_chain,
        joints,
        settings
    )

    preview_chain.curve_plane_center = get_chain_center(joints)

    preview_chain.curve_plane_normal = JOW_math.get_stabilized_curve_plane_normal(
        joints,
        settings
    )

    preview_chain.previous_normals = build_previous_normals(
        joints,
        preview_chain.curve_plane_normal
    )

    root_settings = copy.copy(settings)

    root_settings.custom_object = get_effective_custom_object_for_root(
        preview_chain.root,
        fallback_custom_object=settings.custom_object
    )

    preview_chain.guide = build_preview_guide(preview_chain.root, root_settings)

    orientation_data = JOW_core.compute_linear_chain_orientation(joints, root_settings)

    for entry in orientation_data:
        current_matrix = JOW_maya_transforms.get_world_matrix(entry.joint)

        if current_matrix is None:
            continue

        preview_joint = PreviewJoint()
        preview_joint.name = entry.joint

        preview_joint.is_chain_root = (len(preview_chain.joints) == 0)

        preview_joint.current_matrix = current_matrix
        preview_joint.current_position = position_from_matrix(current_matrix)

        current_x_axis, current_y_axis, current_z_axis = axes_from_matrix(current_matrix)

        preview_joint.current_x_axis = current_x_axis
        preview_joint.current_y_axis = current_y_axis
        preview_joint.current_z_axis = current_z_axis

        preview_joint.matrix = entry.matrix
        preview_joint.position = position_from_matrix(entry.matrix)

        x_axis, y_axis, z_axis = axes_from_matrix(entry.matrix)

        preview_joint.x_axis = x_axis
        preview_joint.y_axis = y_axis
        preview_joint.z_axis = z_axis

        preview_chain.joints.append(preview_joint)
        
    populate_preview_chain_bone_links(preview_chain)
    return preview_chain

def build_preview_chain(root, settings):
    joints = JOW_maya_joints.get_chain_joints(root)
    return build_preview_chain_from_joints(joints, settings)

def get_orient_roots_for_root(root, settings):
    if not root:
        return []

    if not JOW_maya_nodes.exists(root):
        return []

    if getattr(settings, "split_branches", False):
        joint_chains = JOW_maya_joints.get_linear_chains_from_root(
            root
        )

        roots = []

        for joints in joint_chains:
            if not joints:
                continue

            orient_root = joints[0]

            if orient_root in roots:
                continue

            roots.append(orient_root)

        return roots

    return [
        root
    ]


def get_orient_roots_for_roots(roots, settings):
    orient_roots = []

    for root in roots or []:
        roots_for_root = get_orient_roots_for_root(
            root,
            settings
        )

        for orient_root in roots_for_root:
            if orient_root in orient_roots:
                continue

            orient_roots.append(orient_root)

    return orient_roots

def get_preview_joint_chains_for_root(root, settings):
    if getattr(settings, "split_branches", False):
        return JOW_maya_joints.get_linear_chains_from_root(
            root
        )

    joints = JOW_maya_joints.get_chain_joints(
        root
    )

    if not joints:
        return []

    return [
        joints
    ]

def build_preview_chains(settings):
    preview_chains = []
    roots = get_preview_roots()
    
    if not roots:
        return preview_chains
    preview_settings = copy.copy(settings)#avoid mutating.
    if preview_settings.custom_object is None:
        preview_settings.custom_object = get_cached_custom_object()

    for root in roots:
        joint_chains = get_preview_joint_chains_for_root(root, preview_settings)
        for joints in joint_chains:
            preview_chain = build_preview_chain_from_joints(joints, preview_settings)
            if not preview_chain:
                continue
            if not preview_chain.joints:
                continue

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
        if normal is None:
            continue
        position = JOW_maya_transforms.get_world_position(joints[i])

        if position is None:
            continue

        preview_normal = PreviewNormal()
        preview_normal.position = position
        preview_normal.normal = normal

        previous_normals.append(preview_normal)

    return previous_normals


def build_preview_guide(root, settings):
    guide_node = get_effective_custom_object_for_root(
        root,
        fallback_custom_object=settings.custom_object
    )

    if not guide_node:
        return None

    if not JOW_maya_nodes.exists(guide_node):
        return None

    position = JOW_maya_transforms.get_world_position(guide_node)

    if position is None:
        return None

    guide = PreviewGuide()
    guide.name = guide_node
    guide.position = position

    return guide


def set_preview_chain_root_parent_link(preview_chain, joints, settings):
    if not preview_chain:
        return
    if not joints:
        return
    if not getattr(settings, "split_branches", False):
        return
    root = joints[0]
    parent = JOW_maya_joints.get_parent_joint(root)

    if not parent:
        return
    if not JOW_maya_nodes.exists(parent):
        return

    # Only draw this for actual branch roots.
    # If the parent is not a branch joint, this is probably just an
    # externally parented selected root, not a split-child chain.
    if not JOW_maya_joints.is_branch_joint(parent):
        return
    parent_position = JOW_maya_transforms.get_world_position(parent)
    if parent_position is None:
        return

    preview_chain.root_parent = parent
    preview_chain.root_parent_position = parent_position


def populate_preview_chain_bone_links(preview_chain):
    if not preview_chain:
        return

    preview_chain.bone_links = []

    joints_by_name = {}

    for preview_joint in preview_chain.joints:
        if not preview_joint.name:
            continue

        joints_by_name[preview_joint.name] = preview_joint

    for child_name, child_joint in joints_by_name.items():
        parent = JOW_maya_joints.get_parent_joint(
            child_name
        )

        if not parent:
            continue

        parent_joint = joints_by_name.get(
            parent
        )

        if parent_joint is None:
            continue

        preview_chain.bone_links.append(
            (
                parent_joint,
                child_joint
            )
        )