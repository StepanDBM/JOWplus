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

from JOW_ui.JOW_drawables.JOW_grid_drawer import JOWGridDrawer
from JOW_ui.JOW_drawables.JOW_axis_drawer import JOWAxisDrawer
from JOW_ui.JOW_drawables.JOW_joint_drawer import JOWJointDrawer
from JOW_ui.JOW_drawables.JOW_guide_drawer import JOWGuideDrawer
from JOW_ui.JOW_drawables.JOW_plane_drawer import JOWPlaneDrawer
from JOW_ui.JOW_drawables.JOW_overlay_drawer import JOWOverlayDrawer

class JOWViewport(QtWidgets.QFrame):
    joint_clicked = QtCore.Signal(str)
    guide_clicked = QtCore.Signal(str)
    viewport_empty_clicked = QtCore.Signal()

    def __init__(self, parent=None):
        super(JOWViewport, self).__init__(parent)
        self.zoom = 1.0
        self.pan = QtCore.QPointF(0, 0)

        self.view_center_a = 0.0
        self.view_center_b = 0.0
        self.view_scale = 40.0

        self.split_branches = False

        self.last_mouse_pos = None
        self.mouse_press_pos = None
        self.projection_mode = "Orbit"

        self.show_grid = True
        self.show_axis_gizmo = True
        self.show_3d_joints = False
        self.show_overlay = True
        self.show_delta_heatmap = False
        
        self.show_current_axes = True
        self.show_preview_axes = True   

        self.show_curve_plane_surface = True
        self.orient_end_joint = True
        self.apply_target_label = "Cached/Selection"

        self.axis_length = 28
        self.joint_size = 5
        self.selected_joint_size = 8
        self.normal_length = 60

        self.show_root_viz = True
        self.root_bone_width = 5
        self.root_joint_ring_width = 3
        self.root_joint_size_multiplier = 1.45

        self.root_axis_length_multiplier = 1.65
        self.root_axis_width = 3
        self.root_axis_label_offset = 8

        self.selected_guide = None
        self.selected_guides = []
        self.selected_joints = []

        self.selected_joint = None
        self.click_threshold = 6
        self.pick_threshold = 14

        self.secondary_mode = "World"
        self.primary_axis = "X"
        self.secondary_axis = "Y"
        self.flip_plane = False
        self.average_normals = True
        self.orient_end_joint = True
        self.apply_target_label = "Cached Chain"

        self.show_joint_names = False

        self.orbit_yaw = 0.0
        self.orbit_pitch = 0.0
        self.orbit_sensitivity = 0.01
        self.orbit_target = self.vector_from_components(0.0,0.0,0.0)

        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.preview_chains = []

        self.grid_drawer = JOWGridDrawer(self)
        self.axis_drawer = JOWAxisDrawer(self)
        self.joint_drawer = JOWJointDrawer(self)
        self.guide_drawer = JOWGuideDrawer(self)
        self.plane_drawer = JOWPlaneDrawer(self)
        self.overlay_drawer = JOWOverlayDrawer(self)

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
        had_chains = bool(self.preview_chains)
        self.preview_chains = preview_chains
        if preview_chains and not had_chains:
            self.frame_preview()
            return
        self.update()
    def set_show_joint_names(self, state):
        self.show_joint_names = state
        self.update()
    def set_selected_joint(self, joint_name):
        self.selected_joint = joint_name

        if joint_name:
            self.selected_joints = [joint_name]
        else:
            self.selected_joints = []

        self.update()
    def set_selected_joints(self, joint_names):
        clean_joints = []

        for joint_name in joint_names or []:
            if not joint_name:
                continue

            if joint_name in clean_joints:
                continue

            clean_joints.append(joint_name)

        self.selected_joints = clean_joints

        if clean_joints:
            self.selected_joint = clean_joints[-1]
        else:
            self.selected_joint = None

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
        self.selected_joint_size = value + 5
        self.update()
    def set_normal_length(self, value):
        self.normal_length = value
        self.update()
    def set_show_3d_joints(self, state):
        self.show_3d_joints = state
        self.update()
    def set_show_curve_plane_surface(self, state):
        self.show_curve_plane_surface = state
        self.update()
    def set_apply_target_label(self, label):
        self.apply_target_label = label
        self.update()
    def set_overlay_context(self, settings, apply_target_label):
        self.primary_axis = settings.primary_axis
        self.secondary_axis = settings.secondary_axis
        self.flip_plane = settings.flip_plane
        self.average_normals = settings.average_normals
        self.orient_end_joint = settings.orient_end_joint

        self.split_branches = getattr(
            settings,
            "split_branches",
            False
        )

        self.apply_target_label = apply_target_label
        self.update()
    def set_show_current_axes(self, state):
        self.show_current_axes = state
        self.update()
    def set_show_preview_axes(self, state):
        self.show_preview_axes = state
        self.update()
    def set_show_overlay(self, state):
        self.show_overlay = state
        self.update()
    def set_show_delta_heatmap(self, state):
        self.show_delta_heatmap = state
        self.update()
    def set_selected_guide(self, guide_name):
        self.selected_guide = guide_name

        if guide_name:
            self.selected_guides = [guide_name]
        else:
            self.selected_guides = []

        self.update()
    def set_selected_guides(self, guide_names):
        clean_guides = []

        for guide_name in guide_names or []:
            if not guide_name:
                continue

            if guide_name in clean_guides:
                continue

            clean_guides.append(guide_name)

        self.selected_guides = clean_guides

        if clean_guides:
            self.selected_guide = clean_guides[-1]
        else:
            self.selected_guide = None

        self.update()
    def set_orbit_target(self, point):
        if point is None:
            self.orbit_target = self.vector_from_components(0.0,0.0,0.0)
            return

        self.orbit_target = self.vector_from_components(
            point.x,
            point.y,
            point.z
        )

    def is_guide_selected(self, guide_name):
        if not guide_name:
            return False

        if guide_name == self.selected_guide:
            return True

        return guide_name in getattr(
            self,
            "selected_guides",
            []
        )

    def paintEvent(self, event):
        super(JOWViewport, self).paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()

        self.grid_drawer.draw_grid(painter, rect)

        if not self.preview_chains:
            self.draw_empty_state(painter, rect)
            self.axis_drawer.draw_axis_gizmo(painter, rect)
            if self.show_overlay:
                self.overlay_drawer.draw_overlay(painter, rect)
            painter.end()
            return

        points = self.collect_points()

        if not points:
            self.draw_empty_state(painter, rect)
            self.axis_drawer.draw_axis_gizmo(painter, rect)
            if self.show_overlay:
                self.overlay_drawer.draw_overlay(painter, rect)
            painter.end()
            return

        bounds = self.get_bounds(points)
        scale = self.get_scale(bounds, rect)

        for chain in self.preview_chains:
            self.draw_chain(painter, chain, bounds, scale, rect)

        self.axis_drawer.draw_axis_gizmo(painter, rect)
        if self.show_overlay:
            self.overlay_drawer.draw_overlay(painter, rect)

        painter.end()

    def draw_empty_state(self, painter, rect):
        painter.setPen(QtGui.QColor(180, 180, 180))

        painter.drawText(
            rect,
            QtCore.Qt.AlignCenter,
            "\n\n\nSelect joints and <Set Cache From Selection> :)"
        )

    def collect_points(self):
        points = []

        for chain in self.preview_chains:
            for joint in chain.joints:
                if joint.position is None:
                    continue

                points.append(joint.position)

        return points
    
    def collect_frame_points(self):
        points = []

        for chain in self.preview_chains:
            for joint in chain.joints:
                if joint.position is None:
                    continue

                points.append(joint.position)

            if chain.guide and chain.guide.position is not None:
                points.append(chain.guide.position)

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

    def get_world_bounds_center(self, points):
        if not points:
            return self.vector_from_components(0.0,0.0,0.0)

        min_x = min(point.x for point in points)
        max_x = max(point.x for point in points)

        min_y = min(point.y for point in points)
        max_y = max(point.y for point in points)

        min_z = min(point.z for point in points)
        max_z = max(point.z for point in points)

        return self.vector_from_components(
            (min_x + max_x) * 0.5,
            (min_y + max_y) * 0.5,
            (min_z + max_z) * 0.5
        )


    def rotate_point_around_orbit_target(self, point):
        offset = self.vector_from_components(
            point.x - self.orbit_target.x,
            point.y - self.orbit_target.y,
            point.z - self.orbit_target.z
        )

        return self.rotate_vector(offset)

    def get_scale(self, bounds, rect):
        return self.view_scale * self.zoom

    def project_point(self, point, bounds, scale, rect):
        a, b = self.get_projected_values(point)

        x = rect.center().x() + ((a - self.view_center_a) * scale) + self.pan.x()
        y = rect.center().y() - ((b - self.view_center_b) * scale) + self.pan.y()

        return QtCore.QPointF(x, y)

    def project_values(self, a, b, rect, scale):
        x = rect.center().x() + ((a - self.view_center_a) * scale) + self.pan.x()
        y = rect.center().y() - ((b - self.view_center_b) * scale) + self.pan.y()

        return QtCore.QPointF(x, y)

    def screen_to_projected_values(self, x, y, rect, scale):
        a = self.view_center_a + ((x - rect.center().x() - self.pan.x()) / scale)
        b = self.view_center_b - ((y - rect.center().y() - self.pan.y()) / scale)

        return a, b

    def get_visible_projected_range(self, rect, scale):
        a_min, b_max = self.screen_to_projected_values(0, 0, rect, scale)
        a_max, b_min = self.screen_to_projected_values(rect.width(), rect.height(), rect, scale)

        return a_min, a_max, b_min, b_max

    def draw_chain(self, painter, chain, bounds, scale, rect):
        self.plane_drawer.draw_curve_plane_normal_hidden(painter, chain, bounds, scale, rect)
        self.plane_drawer.draw_curve_plane_surface(painter, chain, bounds, scale, rect)
        self.joint_drawer.draw_bones(painter, chain, bounds, scale, rect)
        self.axis_drawer.draw_axes(painter, chain, bounds, scale, rect)

        self.plane_drawer.draw_previous_normals(painter, chain, bounds, scale, rect)

        self.guide_drawer.draw_custom_object_lines(painter, chain, bounds, scale, rect)
        self.guide_drawer.draw_custom_object_marker(painter, chain, bounds, scale, rect)

        self.joint_drawer.draw_joints(painter, chain, bounds, scale, rect)
        self.joint_drawer.draw_joint_names(painter, chain, bounds, scale, rect)
        self.plane_drawer.draw_curve_plane_normal_visible(painter, chain, bounds, scale, rect)

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
        x, y, z = self.rotate_point_around_orbit_target(point)
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

    def frame_preview(self):
        points = self.collect_frame_points()

        if not points:
            return

        focus_point = self.get_world_bounds_center(points)
        self.set_orbit_target(focus_point)

        rect = self.rect()
        bounds = self.get_bounds(points)

        width = max(bounds["max_a"] - bounds["min_a"], 0.001)
        height = max(bounds["max_b"] - bounds["min_b"], 0.001)

        scale_x = (rect.width() * 0.75) / width
        scale_y = (rect.height() * 0.75) / height

        self.view_scale = min(scale_x, scale_y)

        if self.projection_mode == "Orbit":
            self.view_center_a = 0.0
            self.view_center_b = 0.0
        else:
            self.view_center_a = (bounds["min_a"] + bounds["max_a"]) * 0.5
            self.view_center_b = (bounds["min_b"] + bounds["max_b"]) * 0.5

        self.zoom = 1.0
        self.pan = QtCore.QPointF(0,0)

        self.update()

    def frame_selected_joint(self):
        selected_point = self.get_selected_focus_point()
        if selected_point is None:
            return

        self.set_orbit_target(selected_point)
        a, b = self.get_projected_values(selected_point)

        if self.projection_mode == "Orbit":
            self.view_center_a = 0.0
            self.view_center_b = 0.0
        else:
            self.view_center_a = a
            self.view_center_b = b

        self.pan = QtCore.QPointF(0, 0)
        self.update()
    def get_selected_focus_point(self):
        if self.selected_joint:
            for chain in self.preview_chains:
                for joint in chain.joints:
                    if joint.name != self.selected_joint:
                        continue

                    if joint.position is None:
                        return None

                    return joint.position

        if self.selected_guide:
            for chain in self.preview_chains:
                if not chain.guide:
                    continue

                if chain.guide.name != self.selected_guide:
                    continue

                if chain.guide.position is None:
                    return None

                return chain.guide.position

        return None

    ##########################################################
    # Viewport Control
    ##########################################################

    def set_projection_mode(self, mode):
        self.projection_mode = mode
        self.update()


    def reset_view(self):
        self.zoom = 1.0
        self.pan = QtCore.QPointF(0, 0)

        self.view_center_a = 0.0
        self.view_center_b = 0.0

        self.set_orbit_target(self.vector_from_components(0.0, 0.0, 0.0))

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


    def pick_viewport_item(self, screen_pos):
        guide_name = self.guide_drawer.pick_guide(screen_pos)
        if guide_name:
            self.set_selected_guide(guide_name)
            self.set_selected_joint(None)
            self.guide_clicked.emit(guide_name)

            return

        joint_name = self.joint_drawer.pick_joint(screen_pos)
        if joint_name:
            self.set_selected_joint(joint_name)
            self.set_selected_guide(None)
            self.joint_clicked.emit(joint_name)

            return

        self.clear_viewport_selection()
        self.viewport_empty_clicked.emit()

    def clear_viewport_selection(self):
        self.set_selected_joint(None)
        self.set_selected_guide(None)
        self.update()

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
                    self.pick_viewport_item(event.pos())

            self.last_mouse_pos = None
            self.mouse_press_pos = None

        if event.button() == QtCore.Qt.MiddleButton:
            self.last_mouse_pos = None