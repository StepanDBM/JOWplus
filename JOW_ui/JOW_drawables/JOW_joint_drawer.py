try:
    from PySide2 import QtCore
    from PySide2 import QtGui
except ImportError:
    from PySide6 import QtCore
    from PySide6 import QtGui

import math

class JOWJointDrawer:

    def __init__(self, viewport):
        self.viewport = viewport

    def get_bone_links_for_chain(self, chain):
        bone_links = getattr(
            chain,
            "bone_links",
            None
        )

        if bone_links:
            return bone_links

        fallback_links = []

        for i in range(len(chain.joints) - 1):
            fallback_links.append(
                (
                    chain.joints[i],
                    chain.joints[i + 1]
                )
            )

        return fallback_links


    def get_dimmed_branch_child_names(self, chain):
        if getattr(
            self.viewport,
            "split_branches",
            False
        ):
            return []

        bone_links = getattr(
            chain,
            "bone_links",
            None
        )

        if not bone_links:
            return []

        children_by_parent = {}

        for parent_joint, child_joint in bone_links:
            if parent_joint is None:
                continue

            if child_joint is None:
                continue

            if not parent_joint.name:
                continue

            children_by_parent.setdefault(
                parent_joint.name,
                []
            ).append(
                child_joint
            )

        dimmed_child_names = []

        for parent_name, child_joints in children_by_parent.items():
            if len(child_joints) <= 1:
                continue

            for child_joint in child_joints:
                if not child_joint.name:
                    continue

                if child_joint.name in dimmed_child_names:
                    continue

                dimmed_child_names.append(
                    child_joint.name
                )

        return dimmed_child_names


    def is_dimmed_branch_bone(self, child, dimmed_child_names):
        if child is None:
            return False

        if not child.name:
            return False

        return child.name in dimmed_child_names

    def draw_root_joint(self, painter, joint, point):
        root_size = self.viewport.joint_size * getattr(
            self.viewport,
            "root_joint_size_multiplier",
            1.45
        )

        if getattr(self.viewport, "show_delta_heatmap", False):
            self.draw_joint_delta_ring(
                painter,
                joint,
                point,
                selected=False,
                base_radius_override = root_size
            )

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(255, 255, 255),
                getattr(
                    self.viewport,
                    "root_joint_ring_width",
                    3
                )
            )
        )

        painter.setBrush(
            QtGui.QBrush(
                QtGui.QColor(255, 210, 80)
            )
        )

        painter.drawEllipse(
            point,
            root_size,
            root_size
        )

    def is_joint_selected(self, joint_name):
        selected_joints = getattr(
            self.viewport,
            "selected_joints",
            []
        )

        if joint_name in selected_joints:
            return True

        selected_joint = getattr(
            self.viewport,
            "selected_joint",
            None
        )

        return joint_name == selected_joint
    
    def draw_selected_root_joint(self, painter, joint, point):

        root_size = self.viewport.selected_joint_size * getattr(
            self.viewport,
            "root_joint_size_multiplier",
            1.45
        )

        self.draw_joint_delta_ring(
            painter,
            joint,
            point,
            selected=True,
            base_radius_override=root_size
        )

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(255, 245, 180),
                getattr(
                    self.viewport,
                    "root_joint_ring_width",
                    3
                )
            )
        )

        painter.setBrush(
            QtGui.QBrush(
                QtGui.QColor(255, 210, 80)
            )
        )

        painter.drawEllipse(
            point,
            root_size,
            root_size
        )


    def draw_root_parent_link(self, painter, chain, bounds, scale, rect):
        if not getattr(
            self.viewport,
            "show_root_viz",
            True
        ):
            return

        if not getattr(
            chain,
            "root_parent",
            None
        ):
            return

        if getattr(
            chain,
            "root_parent_position",
            None
        ) is None:
            return

        if not chain.joints:
            return

        root_joint = chain.joints[0]

        if root_joint.position is None:
            return

        parent_point = self.viewport.project_point(
            chain.root_parent_position,
            bounds,
            scale,
            rect
        )

        root_point = self.viewport.project_point(
            root_joint.position,
            bounds,
            scale,
            rect
        )

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(230, 230, 230, 150),
                1,
                QtCore.Qt.DotLine
            )
        )

        painter.drawLine(
            parent_point,
            root_point
        )


    def draw_bones(self, painter, chain, bounds, scale, rect):
        self.draw_root_parent_link(
            painter,
            chain,
            bounds,
            scale,
            rect
        )

        if self.viewport.show_3d_joints:
            self.draw_pyramid_bones(
                painter,
                chain,
                bounds,
                scale,
                rect
            )
            return

        bone_links = self.get_bone_links_for_chain(chain)

        dimmed_child_names = self.get_dimmed_branch_child_names(chain)

        for joint, child in bone_links:
            if joint.position is None:
                continue

            if child.position is None:
                continue

            point_a = self.viewport.project_point(
                joint.position,
                bounds,
                scale,
                rect
            )

            point_b = self.viewport.project_point(
                child.position,
                bounds,
                scale,
                rect
            )

            is_root_bone = (
                joint == chain.joints[0] and
                getattr(
                    joint,
                    "is_chain_root",
                    False
                ) and
                getattr(
                    self.viewport,
                    "show_root_viz",
                    True
                )
            )

            is_dimmed = self.is_dimmed_branch_bone(
                child,
                dimmed_child_names
            )

            width = 2
            color = QtGui.QColor(220, 220, 220)

            if is_root_bone:
                width = getattr(
                    self.viewport,
                    "root_bone_width",
                    5
                )

            if is_dimmed:
                width = 1
                color = QtGui.QColor(255, 255, 255, 85)

            painter.setPen(
                QtGui.QPen(
                    color,
                    width
                )
            )

            painter.drawLine(point_a, point_b)

    def draw_pyramid_bones(self, painter, chain, bounds, scale, rect):
        bone_links = getattr(
            chain,
            "bone_links",
            None
        )

        dimmed_child_names = self.get_dimmed_branch_child_names(chain)

        if bone_links:
            for joint, child in bone_links:
                is_root_bone = (
                    joint == chain.joints[0] and
                    getattr(
                        joint,
                        "is_chain_root",
                        False
                    ) and
                    getattr(
                        self.viewport,
                        "show_root_viz",
                        True
                    )
                )
                is_dimmed = self.is_dimmed_branch_bone(child, dimmed_child_names)

                self.draw_pyramid_bone(
                    painter,
                    joint,
                    child,
                    bounds,
                    scale,
                    rect,
                    is_root_bone=is_root_bone,
                    dimmed=is_dimmed
                )

            return

        for i in range(len(chain.joints) - 1):
            joint = chain.joints[i]
            child = chain.joints[i + 1]

            is_root_bone = (
                i == 0 and
                getattr(
                    joint,
                    "is_chain_root",
                    False
                ) and
                getattr(
                    self.viewport,
                    "show_root_viz",
                    True
                )
            )

            self.draw_pyramid_bone(
                painter,
                joint,
                child,
                bounds,
                scale,
                rect,
                is_root_bone=is_root_bone
            )

    def draw_pyramid_bone(
        self,
        painter,
        joint,
        child,
        bounds,
        scale,
        rect,
        is_root_bone=False,
        dimmed=False
    ):
        if joint.position is None:
            return

        if child.position is None:
            return

        base_axis_a, base_axis_b = self.get_pyramid_base_axes(
            joint,
            child
        )

        if base_axis_a is None or base_axis_b is None:
            self.draw_fallback_bone_line(
                painter,
                joint,
                child,
                bounds,
                scale,
                rect,
                dimmed=dimmed
            )
            return

        size_multiplier = 1.4

        if dimmed:
            size_multiplier = 0.75

        world_size = max(
            0.001,
            (self.viewport.joint_size * size_multiplier) / max(scale, 0.001)
        )

        center = joint.position
        tip = child.position

        corner_a = center + (base_axis_a * world_size) + (base_axis_b * world_size)
        corner_b = center + (base_axis_a * world_size) - (base_axis_b * world_size)
        corner_c = center - (base_axis_a * world_size) - (base_axis_b * world_size)
        corner_d = center - (base_axis_a * world_size) + (base_axis_b * world_size)

        screen_a = self.viewport.project_point(corner_a, bounds, scale, rect)
        screen_b = self.viewport.project_point(corner_b, bounds, scale, rect)
        screen_c = self.viewport.project_point(corner_c, bounds, scale, rect)
        screen_d = self.viewport.project_point(corner_d, bounds, scale, rect)
        screen_tip = self.viewport.project_point(tip, bounds, scale, rect)

        base_polygon = QtGui.QPolygonF([
            screen_a,
            screen_b,
            screen_c,
            screen_d
        ])

        outline_width = 1
        line_color = QtGui.QColor(210, 210, 210, 255)
        fill_color = QtGui.QColor(120, 120, 120, 45)

        if is_root_bone:
            outline_width = 3
            line_color = QtGui.QColor(180, 235, 255)
            fill_color = QtGui.QColor(120, 120, 120, 45)

        if dimmed:
            outline_width = 1
            line_color = QtGui.QColor(255, 255, 255, 80)
            fill_color = QtGui.QColor(255, 255, 255, 10)

        painter.setPen(QtGui.QPen(line_color, outline_width))

        painter.setBrush(QtGui.QBrush(fill_color))

        painter.drawPolygon(base_polygon)
        painter.drawLine(screen_a, screen_tip)
        painter.drawLine(screen_b, screen_tip)
        painter.drawLine(screen_c, screen_tip)
        painter.drawLine(screen_d, screen_tip)
        painter.drawLine(screen_a, screen_b)
        painter.drawLine(screen_b, screen_c)
        painter.drawLine(screen_c, screen_d)
        painter.drawLine(screen_d,screen_a)

    def draw_fallback_bone_line(
        self,
        painter,
        joint,
        child,
        bounds,
        scale,
        rect,
        dimmed=False
    ):
        point_a = self.viewport.project_point(
            joint.position,
            bounds,
            scale,
            rect
        )

        point_b = self.viewport.project_point(
            child.position,
            bounds,
            scale,
            rect
        )

        color = QtGui.QColor(220, 220, 220)
        width = 2

        if dimmed:
            color = QtGui.QColor(255, 255, 255, 80)
            width = 1

        painter.setPen(
            QtGui.QPen(
                color,
                width
            )
        )

        painter.drawLine(
            point_a,
            point_b
        )

    def get_pyramid_base_axes(self, joint, child):
        if joint.x_axis is None:
            return None, None

        if joint.y_axis is None:
            return None, None

        if joint.z_axis is None:
            return None, None

        forward = child.position - joint.position

        if forward.length() < 0.0001:
            return joint.x_axis, joint.y_axis

        forward = forward.normal()

        candidates = [
            joint.x_axis,
            joint.y_axis,
            joint.z_axis
        ]

        candidates.sort(
            key=lambda axis: abs(axis * forward)
        )

        return candidates[0], candidates[1]

    def draw_joints(self, painter, chain, bounds, scale, rect):
        for joint in chain.joints:
            if joint.position is None:
                continue

            point = self.viewport.project_point(
                joint.position,
                bounds,
                scale,
                rect
            )

            is_selected = self.is_joint_selected(joint.name)

            is_chain_root = (
                getattr(
                    joint,
                    "is_chain_root",
                    False
                ) and
                getattr(
                    self.viewport,
                    "show_root_viz",
                    True
                )
            )
            if is_selected and is_chain_root:
                self.draw_selected_root_joint(painter, joint,point)
            elif is_selected:
                self.draw_selected_joint(painter, joint, point)
            elif is_chain_root:
                self.draw_root_joint(painter, joint, point)
            else:
                self.draw_regular_joint(painter, joint, point)

    def draw_regular_joint(self, painter, joint, point):
        if getattr(self.viewport, "show_delta_heatmap", False):
            self.draw_joint_delta_ring(
                painter,
                joint,
                point,
                selected=False
            )

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(255, 255, 255),
                1
            )
        )

        painter.setBrush(
            QtGui.QBrush(
                QtGui.QColor(255, 210, 80)
            )
        )

        painter.drawEllipse(
            point,
            self.viewport.joint_size,
            self.viewport.joint_size
        )


    def draw_selected_joint(self, painter, joint, point):
        self.draw_joint_delta_ring(
            painter,
            joint,
            point,
            selected=True
        )
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 210, 80)))

        painter.drawEllipse(
            point,
            self.viewport.selected_joint_size,
            self.viewport.selected_joint_size
        )

    def draw_joint_delta_ring(self, painter, joint, point, selected=False, base_radius_override=None):
        delta_color = self.get_joint_delta_color(joint)

        if base_radius_override is not None:
            base_radius = base_radius_override + 2
        elif selected:
            base_radius = self.viewport.selected_joint_size
        else:
            base_radius = self.viewport.joint_size

        if selected:
            radius = base_radius + 6
            width = 4
        else:
            radius = base_radius + 5
            width = 2

        painter.setPen(
            QtGui.QPen(
                delta_color,
                width
            )
        )

        painter.setBrush(
            QtCore.Qt.NoBrush
        )

        painter.drawEllipse(
            point,
            radius,
            radius
        )

    def draw_joint_names(self, painter, chain, bounds, scale, rect):
        if not self.viewport.show_joint_names:
            return

        painter.setPen(QtGui.QColor(220, 220, 220))

        for joint in chain.joints:
            if joint.position is None:
                continue

            point = self.viewport.project_point(joint.position, bounds, scale, rect)

            painter.drawText(
                point + QtCore.QPointF(8, -8),
                joint.name.split("|")[-1]
            )

    def get_joint_pick_radius(self, joint):
        is_selected = self.is_joint_selected(
            joint.name
        )

        is_chain_root = (
            getattr(
                joint,
                "is_chain_root",
                False
            ) and
            getattr(
                self.viewport,
                "show_root_viz",
                True
            )
        )

        if is_selected:
            base_radius = self.viewport.selected_joint_size
        else:
            base_radius = self.viewport.joint_size

        if is_chain_root:
            base_radius *= getattr(
                self.viewport,
                "root_joint_size_multiplier",
                1.45
            )

        padding = getattr(
            self.viewport,
            "joint_pick_padding",
            4
        )

        return base_radius + padding

    def find_joint_at_screen_pos(self, screen_pos):
        bounds, scale, rect = self.viewport.get_current_view_data()

        if not bounds:
            return None

        closest_joint = None
        closest_distance = None
        closest_pick_radius = None

        for chain in self.viewport.preview_chains:
            for joint in chain.joints:
                if joint.position is None:
                    continue

                point = self.viewport.project_point(
                    joint.position,
                    bounds,
                    scale,
                    rect
                )

                delta_x = point.x() - screen_pos.x()
                delta_y = point.y() - screen_pos.y()

                distance = (delta_x ** 2 + delta_y ** 2) ** 0.5

                pick_radius = self.get_joint_pick_radius(joint)

                if distance > pick_radius:
                    continue

                if closest_distance is None or distance < closest_distance:
                    closest_distance = distance
                    closest_pick_radius = pick_radius
                    closest_joint = joint

        return closest_joint


    def pick_joint(self, screen_pos):
        joint = self.find_joint_at_screen_pos(screen_pos)

        if not joint:
            return None

        return joint.name

    def get_joint_delta_color(self, joint):
        delta = self.get_joint_orientation_delta(
            joint
        )

        if delta is None:
            return QtGui.QColor(255, 255, 255)

        if delta < 5.0:
            return QtGui.QColor(120, 255, 150)

        if delta < 25.0:
            return QtGui.QColor(220, 220, 220)

        if delta < 60.0:
            return QtGui.QColor(255, 170, 70)

        return QtGui.QColor(255, 80, 80)


    def get_joint_orientation_delta(self, joint):
        required_vectors = [
            getattr(joint, "current_x_axis", None),
            getattr(joint, "current_y_axis", None),
            getattr(joint, "current_z_axis", None),
            joint.x_axis,
            joint.y_axis,
            joint.z_axis
        ]

        for vector in required_vectors:
            if vector is None:
                return None

        x_delta = self.get_vector_angle_degrees(
            joint.current_x_axis,
            joint.x_axis
        )

        y_delta = self.get_vector_angle_degrees(
            joint.current_y_axis,
            joint.y_axis
        )

        z_delta = self.get_vector_angle_degrees(
            joint.current_z_axis,
            joint.z_axis
        )

        if x_delta is None or y_delta is None or z_delta is None:
            return None

        return max(
            x_delta,
            y_delta,
            z_delta
        )


    def get_vector_angle_degrees(self, vector_a, vector_b):
        if vector_a is None or vector_b is None:
            return None

        if vector_a.length() < 0.0001:
            return None

        if vector_b.length() < 0.0001:
            return None

        a = vector_a.normal()
        b = vector_b.normal()

        dot = a * b

        dot = max(
            -1.0,
            min(
                1.0,
                dot
            )
        )

        return math.degrees(math.acos(dot))