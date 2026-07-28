# NEx_SDBM/ui/main_window.py

try:
    from PySide2 import QtWidgets
    from PySide2 import QtCore
    from PySide2 import QtGui
except ImportError:
    from PySide6 import QtWidgets
    from PySide6 import QtCore
    from PySide6 import QtGui


import math as py_math

class JOWViewport(QtWidgets.QFrame):
    joint_clicked = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(JOWViewport, self).__init__(parent)
        self.zoom = 1.0
        self.pan = QtCore.QPointF(0, 0)
        self.last_mouse_pos = None
        self.mouse_press_pos = None
        self.projection_mode = "XY"

        self.show_grid = True
        self.show_axis_gizmo = True

        self.axis_length = 28
        self.joint_size = 5
        self.selected_joint_size = 8
        self.normal_length = 60

        self.selected_joint = None
        self.click_threshold = 6
        self.pick_threshold = 14

        self.secondary_mode = "World"

        self.show_joint_names = False

        self.orbit_yaw = 0.0
        self.orbit_pitch = 0.0
        self.orbit_sensitivity = 0.01

        self.setMouseTracking(True)

        self.preview_chains = []

        self.setMinimumHeight(360)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet("background-color: #202020;")

    def vector_from_components(self, x, y, z):
        class SimpleVector:
            pass

        vector = SimpleVector()
        vector.x = x
        vector.y = y
        vector.z = z

        return vector

    def set_secondary_mode(self, mode):
        self.secondary_mode = mode
        self.update()
    def set_preview_chains(self, preview_chains):
        self.preview_chains = preview_chains
        self.update()
    def set_show_joint_names(self, state):
        self.show_joint_names = state
        self.update()
    def set_selected_joint(self, joint_name):
        self.selected_joint = joint_name
        self.update()
    def set_show_grid(self, state):
        self.show_grid = state
        self.update()
    def set_show_axis_gizmo(self, state):
        self.show_axis_gizmo = state
        self.update()
    def set_axis_length(self, value):
        self.axis_length = value
        self.update()
    def set_joint_size(self, value):
        self.joint_size = value
        self.selected_joint_size = value + 3
        self.update()
    def set_normal_length(self, value):
        self.normal_length = value
        self.update()

    def paintEvent(self, event):
        super(JOWViewport, self).paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()

        if not self.preview_chains:
            self.draw_empty_state(painter, rect)
            painter.end()
            return

        points = self.collect_points()

        if not points:
            self.draw_empty_state(painter, rect)
            painter.end()
            return

        bounds = self.get_bounds(points)
        scale = self.get_scale(bounds, rect)

        self.draw_grid(painter, rect)

        for chain in self.preview_chains:
            self.draw_chain(painter, chain, bounds, scale, rect)

        self.draw_axis_gizmo(painter, rect)
        self.draw_overlay(painter, rect)

        painter.end()

    def draw_empty_state(self, painter, rect):
        painter.setPen(QtGui.QColor(180, 180, 180))

        painter.drawText(
            rect,
            QtCore.Qt.AlignCenter,
            ":)\n\nViewport Coming Soon\n\nSelect joints and refresh preview"
        )

    def collect_points(self):
        points = []

        for chain in self.preview_chains:
            for joint in chain.joints:
                if joint.position:
                    points.append(joint.position)

        return points

    def get_bounds(self, points):
        projected = [self.get_projected_values(p) for p in points]

        min_a = min(p[0] for p in projected)
        max_a = max(p[0] for p in projected)

        min_b = min(p[1] for p in projected)
        max_b = max(p[1] for p in projected)

        return {
            "min_a": min_a,
            "max_a": max_a,
            "min_b": min_b,
            "max_b": max_b
        }
    def get_scale(self, bounds, rect):
        width = max(bounds["max_a"] - bounds["min_a"], 0.001)
        height = max(bounds["max_b"] - bounds["min_b"], 0.001)

        scale_x = (rect.width() * 0.75) / width
        scale_y = (rect.height() * 0.75) / height

        return min(scale_x, scale_y) * self.zoom

    def project_point(self, point, bounds, scale, rect):
        a, b = self.get_projected_values(point)

        center_a = (bounds["min_a"] + bounds["max_a"]) * 0.5
        center_b = (bounds["min_b"] + bounds["max_b"]) * 0.5

        x = rect.center().x() + ((a - center_a) * scale) + self.pan.x()
        y = rect.center().y() - ((b - center_b) * scale) + self.pan.y()

        return QtCore.QPointF(x, y)


    def draw_grid(self, painter, rect):
        if not self.show_grid:
            return

        spacing = 40

        painter.setPen(QtGui.QPen(QtGui.QColor(45, 45, 45), 1))

        start_x = int(self.pan.x()) % spacing
        start_y = int(self.pan.y()) % spacing

        x = start_x

        while x < rect.width():
            painter.drawLine(x, 0, x, rect.height())
            x += spacing

        y = start_y

        while y < rect.height():
            painter.drawLine(0, y, rect.width(), y)
            y += spacing

        painter.setPen(QtGui.QPen(QtGui.QColor(70, 70, 70), 1))

        painter.drawLine(rect.center().x() + self.pan.x(), 0, rect.center().x() + self.pan.x(), rect.height())
        painter.drawLine(0, rect.center().y() + self.pan.y(), rect.width(), rect.center().y() + self.pan.y())

    def draw_axis_gizmo(self, painter, rect):
        if not self.show_axis_gizmo:
            return

        origin = QtCore.QPointF(
            rect.right() - 70,
            rect.bottom() - 55
        )

        length = 32

        axes = [
            ("X", self.vector_from_components(1, 0, 0), QtGui.QColor(255, 80, 80)),
            ("Y", self.vector_from_components(0, 1, 0), QtGui.QColor(80, 255, 80)),
            ("Z", self.vector_from_components(0, 0, 1), QtGui.QColor(80, 140, 255))
        ]

        for label, axis, color in axes:
            axis_a, axis_b = self.project_gizmo_axis(axis, label)

            end = QtCore.QPointF(
                origin.x() + axis_a * length,
                origin.y() - axis_b * length
            )

            painter.setPen(QtGui.QPen(color, 2))
            painter.drawLine(origin, end)

            painter.setPen(color)
            painter.drawText(
                end + QtCore.QPointF(4, -4),
                label
            )

        painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 1))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(220, 220, 220)))
        painter.drawEllipse(origin, 3, 3)

    def draw_chain(self, painter, chain, bounds, scale, rect):
        self.draw_bones(painter, chain, bounds, scale, rect)
        self.draw_axes(painter, chain, bounds, scale, rect)
        self.draw_curve_plane_normal(painter, chain, bounds, scale, rect)
        self.draw_previous_normals(painter, chain, bounds, scale, rect)
        self.draw_custom_object_lines(painter, chain, bounds, scale, rect)
        self.draw_custom_object_marker(painter, chain, bounds, scale, rect)
        self.draw_joints(painter, chain, bounds, scale, rect)
        self.draw_joint_names(painter, chain, bounds, scale, rect)

    def draw_bones(self, painter, chain, bounds, scale, rect):
        painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 2))

        for i in range(len(chain.joints) - 1):
            a = chain.joints[i]
            b = chain.joints[i + 1]

            point_a = self.project_point(a.position, bounds, scale, rect)
            point_b = self.project_point(b.position, bounds, scale, rect)

            painter.drawLine(point_a, point_b)

    def draw_joints(self, painter, chain, bounds, scale, rect):
        for joint in chain.joints:
            point = self.project_point(joint.position, bounds, scale, rect)

            if joint.name == self.selected_joint:
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 90, 40)))
                painter.drawEllipse(point, self.selected_joint_size, self.selected_joint_size)
            else:
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 1))
                painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 210, 80)))
                painter.drawEllipse(point, self.joint_size, self.joint_size)

    def draw_axes(self, painter, chain, bounds, scale, rect):
        for joint in chain.joints:
            origin = self.project_point(joint.position, bounds, scale, rect)

            show_labels = (joint.name == self.selected_joint)

            self.draw_axis(
                painter,
                origin,
                joint.x_axis,
                self.axis_length,
                QtGui.QColor(255, 80, 80),
                "X" if show_labels else None
            )

            self.draw_axis(
                painter,
                origin,
                joint.y_axis,
                self.axis_length,
                QtGui.QColor(80, 255, 80),
                "Y" if show_labels else None
            )

            self.draw_axis(
                painter,
                origin,
                joint.z_axis,
                self.axis_length,
                QtGui.QColor(80, 140, 255),
                "Z" if show_labels else None
            )

    def draw_axis(self, painter, origin, axis, length, color, label=None):
        if not axis:
            return

        axis_a, axis_b = self.project_axis(axis)

        painter.setPen(QtGui.QPen(color, 2))

        end = QtCore.QPointF(
            origin.x() + axis_a * length,
            origin.y() - axis_b * length
        )

        painter.drawLine(origin, end)

        if label:
            painter.setPen(color)
            painter.drawText(
                end + QtCore.QPointF(4, -4),
                label
            )

    def draw_curve_plane_normal(self, painter, chain, bounds, scale, rect):
        if self.secondary_mode != "Curve Plane":
            return

        if not chain.curve_plane_center:
            return

        if not chain.curve_plane_normal:
            return

        origin = self.project_point(chain.curve_plane_center, bounds, scale, rect)

        axis_a, axis_b = self.project_axis(chain.curve_plane_normal)

        length = self.normal_length

        end = QtCore.QPointF(
            origin.x() + axis_a * length,
            origin.y() - axis_b * length
        )

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 230, 80), 3))
        painter.drawLine(origin, end)

        painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 230, 80)))
        painter.drawEllipse(end, 4, 4)

    def draw_overlay(self, painter, rect):
        painter.setPen(QtGui.QColor(200, 200, 200))

        text = "Projection: {}   Mode: {}   Chains: {}".format(
            self.projection_mode,
            self.secondary_mode,
            len(self.preview_chains)
        )

        painter.drawText(
            rect.adjusted(10, 10, -10, -10),
            QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft,
            text
        )

    def draw_previous_normals(self, painter, chain, bounds, scale, rect):
        if self.secondary_mode != "Previous":
            return

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 180, 60), 2))

        length = self.normal_length

        for previous_normal in chain.previous_normals:
            if not previous_normal.position:
                continue

            if not previous_normal.normal:
                continue

            origin = self.project_point(previous_normal.position, bounds, scale, rect)

            axis_a, axis_b = self.project_axis(previous_normal.normal)

            end = QtCore.QPointF(
                origin.x() + axis_a * length,
                origin.y() - axis_b * length
            )

            painter.drawLine(origin, end)

            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 180, 60)))
            painter.drawEllipse(end, 3, 3)

    def draw_custom_object_marker(self, painter, chain, bounds, scale, rect):
        if self.secondary_mode != "Custom Object":
            return

        if not chain.guide:
            return

        if not chain.guide.position:
            return

        point = self.project_point(chain.guide.position, bounds, scale, rect)

        painter.setPen(QtGui.QPen(QtGui.QColor(230, 160, 255), 2))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(130, 60, 180)))

        painter.drawEllipse(point, 7, 7)

        if chain.guide.name:
            painter.drawText(
                point + QtCore.QPointF(10, -10),
                chain.guide.name.split("|")[-1]
            )

    def draw_custom_object_lines(self, painter, chain, bounds, scale, rect):
        if self.secondary_mode != "Custom Object":
            return

        if not chain.guide:
            return

        if not chain.guide.position:
            return

        guide_point = self.project_point(chain.guide.position, bounds, scale, rect)

        painter.setPen(QtGui.QPen(QtGui.QColor(200, 120, 255), 1, QtCore.Qt.DashLine))

        for joint in chain.joints:
            if not joint.position:
                continue

            joint_point = self.project_point(joint.position, bounds, scale, rect)

            painter.drawLine(joint_point, guide_point)

    def draw_joint_names(self, painter, chain, bounds, scale, rect):
        if not self.show_joint_names:
            return

        painter.setPen(QtGui.QColor(220, 220, 220))

        for joint in chain.joints:
            if not joint.position:
                continue

            point = self.project_point(joint.position, bounds, scale, rect)

            painter.drawText(
                point + QtCore.QPointF(8, -8),
                joint.name.split("|")[-1]
            )


    ##########################################################
    # Projections / Vector transforms
    ##########################################################
    def rotate_vector(self, vector):
        yaw = self.orbit_yaw
        pitch = self.orbit_pitch

        cos_yaw = py_math.cos(yaw)
        sin_yaw = py_math.sin(yaw)

        cos_pitch = py_math.cos(pitch)
        sin_pitch = py_math.sin(pitch)

        x = vector.x
        y = vector.y
        z = vector.z

        rotated_x = (x * cos_yaw) + (z * sin_yaw)
        rotated_z = (-x * sin_yaw) + (z * cos_yaw)
        rotated_y = y

        final_y = (rotated_y * cos_pitch) - (rotated_z * sin_pitch)
        final_z = (rotated_y * sin_pitch) + (rotated_z * cos_pitch)

        return rotated_x, final_y, final_z


    def get_orbit_values(self, point):
        x, y, z = self.rotate_vector(point)
        return x, y

    def get_projected_values(self, point):
        if self.projection_mode == "XY":
            return point.x, point.y

        if self.projection_mode == "XZ":
            return point.x, -point.z

        if self.projection_mode == "ZY":
            return -point.z, point.y

        if self.projection_mode == "Orbit":
            return self.get_orbit_values(point)

        return point.x, point.y

    def project_axis(self, axis):
        if self.projection_mode == "XY":
            return axis.x, axis.y

        if self.projection_mode == "XZ":
            return axis.x, -axis.z

        if self.projection_mode == "ZY":
            return axis.z, axis.y

        if self.projection_mode == "Orbit":
            x, y, z = self.rotate_vector(axis)
            return x, y

        return axis.x, axis.y

    def project_gizmo_axis(self, axis, label):
        axis_a, axis_b = self.project_axis(axis)

        if self.projection_mode == "ZY" and label == "Z":
            axis_a *= -1

        return axis_a, axis_b

    def frame_preview(self):
        self.zoom = 1.0
        self.pan = QtCore.QPointF(0, 0)
        self.update()


    def frame_selected_joint(self):
        if not self.selected_joint:
            return

        bounds, scale, rect = self.get_current_view_data()

        if not bounds:
            return

        for chain in self.preview_chains:
            for joint in chain.joints:
                if joint.name != self.selected_joint:
                    continue

                point = self.project_point(joint.position, bounds, scale, rect)

                self.pan += QtCore.QPointF(
                    rect.center().x() - point.x(),
                    rect.center().y() - point.y()
                )

                self.update()
                return


    ##########################################################
    # Viewport Control
    ##########################################################

    def set_projection_mode(self, mode):
        self.projection_mode = mode
        self.update()


    def reset_view(self):
        self.zoom = 1.0
        self.pan = QtCore.QPointF(0, 0)
        self.orbit_yaw = 0.0
        self.orbit_pitch = 0.0
        self.update()

    def get_current_view_data(self):
        points = self.collect_points()

        if not points:
            return None, None, None

        rect = self.rect()
        bounds = self.get_bounds(points)
        scale = self.get_scale(bounds, rect)

        return bounds, scale, rect


    def find_joint_at_screen_pos(self, screen_pos):
        bounds, scale, rect = self.get_current_view_data()

        if not bounds:
            return None

        closest_joint = None
        closest_distance = None

        for chain in self.preview_chains:
            for joint in chain.joints:
                if not joint.position:
                    continue

                point = self.project_point(joint.position, bounds, scale, rect)

                delta_x = point.x() - screen_pos.x()
                delta_y = point.y() - screen_pos.y()

                distance = (delta_x ** 2 + delta_y ** 2) ** 0.5

                if closest_distance is None or distance < closest_distance:
                    closest_distance = distance
                    closest_joint = joint

        if closest_distance is not None and closest_distance <= self.pick_threshold:
            return closest_joint

        return None


    def pick_joint(self, screen_pos):
        joint = self.find_joint_at_screen_pos(screen_pos)

        if not joint:
            return

        self.set_selected_joint(joint.name)
        self.joint_clicked.emit(joint.name)

    ##########################################################
    # Mouse Events
    ##########################################################

    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        if delta > 0:
            self.zoom *= 1.1
        else:
            self.zoom /= 1.1

        self.zoom = max(0.05, min(self.zoom, 50.0))
        self.update()


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self.last_mouse_pos = event.pos()

        if event.button() == QtCore.Qt.LeftButton:
            self.last_mouse_pos = event.pos()
            self.mouse_press_pos = event.pos()


    def mouseMoveEvent(self, event):
        if self.last_mouse_pos is None:
            return

        delta = event.pos() - self.last_mouse_pos

        if event.buttons() & QtCore.Qt.MiddleButton:
            self.pan += QtCore.QPointF(delta.x(), delta.y())
            self.last_mouse_pos = event.pos()
            self.update()
            return

        if event.buttons() & QtCore.Qt.LeftButton:
            if self.projection_mode == "Orbit":
                self.orbit_yaw += delta.x() * self.orbit_sensitivity
                self.orbit_pitch += delta.y() * self.orbit_sensitivity

                self.orbit_pitch = max(-1.5, min(self.orbit_pitch, 1.5))

                self.last_mouse_pos = event.pos()
                self.update()


    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.mouse_press_pos:
                delta = event.pos() - self.mouse_press_pos
                distance = (delta.x() ** 2 + delta.y() ** 2) ** 0.5

                if distance <= self.click_threshold:
                    self.pick_joint(event.pos())

            self.last_mouse_pos = None
            self.mouse_press_pos = None

        if event.button() == QtCore.Qt.MiddleButton:
            self.last_mouse_pos = None