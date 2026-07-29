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

    def draw_bones(self, painter, chain, bounds, scale, rect):
        if self.viewport.show_3d_joints:
            self.draw_pyramid_bones(painter, chain, bounds, scale, rect)
            return

        painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 2))

        for i in range(len(chain.joints) - 1):
            a = chain.joints[i]
            b = chain.joints[i + 1]

            point_a = self.viewport.project_point(a.position, bounds, scale, rect)
            point_b = self.viewport.project_point(b.position, bounds, scale, rect)

            painter.drawLine(point_a, point_b)

    def draw_pyramid_bones(self, painter, chain, bounds, scale, rect):
        for i in range(len(chain.joints) - 1):
            joint = chain.joints[i]
            child = chain.joints[i + 1]

            self.draw_pyramid_bone(
                painter,
                joint,
                child,
                bounds,
                scale,
                rect
            )

    def draw_pyramid_bone(self, painter, joint, child, bounds, scale, rect):
        if not joint.position:
            return

        if child.position is None:
            return

        base_axis_a, base_axis_b = self.get_pyramid_base_axes(joint, child)

        if not base_axis_a or not base_axis_b:
            self.draw_fallback_bone_line(painter, joint, child, bounds, scale, rect)
            return

        world_size = max(
            0.001,
            (self.viewport.joint_size * 1.4) / max(scale, 0.001)
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

        painter.setPen(QtGui.QPen(QtGui.QColor(210, 210, 210), 1))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(120, 120, 120, 45)))

        painter.drawPolygon(base_polygon)

        painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 1))

        painter.drawLine(screen_a, screen_tip)
        painter.drawLine(screen_b, screen_tip)
        painter.drawLine(screen_c, screen_tip)
        painter.drawLine(screen_d, screen_tip)

        painter.drawLine(screen_a, screen_b)
        painter.drawLine(screen_b, screen_c)
        painter.drawLine(screen_c, screen_d)
        painter.drawLine(screen_d, screen_a)

    def draw_fallback_bone_line(self, painter, joint, child, bounds, scale, rect):
        point_a = self.viewport.project_point(joint.position, bounds, scale, rect)
        point_b = self.viewport.project_point(child.position, bounds, scale, rect)

        painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 2))
        painter.drawLine(point_a, point_b)

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

            if joint.name == self.viewport.selected_joint:
                self.draw_selected_joint(
                    painter,
                    joint,
                    point
                )
            else:
                self.draw_regular_joint(
                    painter,
                    joint,
                    point
                )

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
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 90, 40)))

        painter.drawEllipse(
            point,
            self.viewport.selected_joint_size,
            self.viewport.selected_joint_size
        )

    def draw_joint_delta_ring(self, painter, joint, point, selected=False):
        delta_color = self.get_joint_delta_color(joint)

        if selected:
            radius = self.viewport.selected_joint_size + 4
            width = 4
        else:
            radius = self.viewport.joint_size + 4
            width = 2

        painter.setPen(
            QtGui.QPen(
                delta_color,
                width
            )
        )

        painter.setBrush(QtCore.Qt.NoBrush)

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

    def find_joint_at_screen_pos(self, screen_pos):
        bounds, scale, rect = self.viewport.get_current_view_data()

        if not bounds:
            return None

        closest_joint = None
        closest_distance = None

        for chain in self.viewport.preview_chains:
            for joint in chain.joints:
                if joint.position is None:
                    continue

                point = self.viewport.project_point(joint.position, bounds, scale, rect)

                delta_x = point.x() - screen_pos.x()
                delta_y = point.y() - screen_pos.y()

                distance = (delta_x ** 2 + delta_y ** 2) ** 0.5

                if closest_distance is None or distance < closest_distance:
                    closest_distance = distance
                    closest_joint = joint

        if closest_distance is not None and closest_distance <= self.viewport.pick_threshold:
            return closest_joint

        return None

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

        return math.degrees(
            math.acos(
                dot
            )
        )