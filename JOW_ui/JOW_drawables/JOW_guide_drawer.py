try:
    from PySide2 import QtCore
    from PySide2 import QtGui
except ImportError:
    from PySide6 import QtCore
    from PySide6 import QtGui

from JOW_ui.JOW_gl import JOW_preview

class JOWGuideDrawer:

    def __init__(self, viewport):
        self.viewport = viewport

    def draw_custom_object_lines(self, painter, chain, bounds, scale, rect):
        if self.viewport.secondary_mode != "Custom Object":
            return

        if not chain.guide:
            return

        if chain.guide.position is None:
            return
        is_selected = self.is_guide_selected(chain.guide.name)
        guide_point = self.viewport.project_point(
            chain.guide.position,
            bounds,
            scale,
            rect
        )

        if is_selected:
            color = QtGui.QColor(255, 220, 120, 180)
            width = 2
        else:
            color = QtGui.QColor(200, 120, 255, 120)
            width = 1

        painter.setPen(
            QtGui.QPen(
                color,
                width,
                QtCore.Qt.DashLine
            )
        )

        for joint in chain.joints:
            if joint.position is None:
                continue

            joint_point = self.viewport.project_point(
                joint.position,
                bounds,
                scale,
                rect
            )

            painter.drawLine(
                joint_point,
                guide_point
            )

    def draw_custom_object_marker(self, painter, chain, bounds, scale, rect):
        if self.viewport.secondary_mode != "Custom Object":
            return

        if not chain.guide:
            return

        if chain.guide.position is None:
            return

        point = self.viewport.project_point(
            chain.guide.position,
            bounds,
            scale,
            rect
        )
        is_selected = self.is_guide_selected(chain.guide.name)
        if is_selected:
            self.draw_selected_guide_marker(
                painter,
                chain,
                point
            )
        else:
            self.draw_regular_guide_marker(
                painter,
                chain,
                point
            )

    def draw_regular_guide_marker(self, painter, chain, point):
        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(230, 160, 255),
                2
            )
        )

        painter.setBrush(
            QtGui.QBrush(
                QtGui.QColor(130, 60, 180)
            )
        )

        painter.drawEllipse(
            point,
            7,
            7
        )

        self.draw_guide_label(
            painter,
            chain,
            point,
            QtGui.QColor(230, 160, 255)
        )

    def draw_selected_guide_marker(self, painter, chain, point):
        halo_color = QtGui.QColor(255, 220, 120, 220)
        fill_color = QtGui.QColor(180, 90, 255)
        outline_color = QtGui.QColor(255, 245, 180)

        painter.setPen(
            QtGui.QPen(
                halo_color,
                3
            )
        )

        painter.setBrush(
            QtCore.Qt.NoBrush
        )

        painter.drawEllipse(
            point,
            13,
            13
        )

        painter.setPen(
            QtGui.QPen(
                outline_color,
                2
            )
        )

        painter.setBrush(
            QtGui.QBrush(
                fill_color
            )
        )

        painter.drawEllipse(
            point,
            8,
            8
        )

        self.draw_guide_label(
            painter,
            chain,
            point,
            outline_color
        )
    def draw_guide_label(self, painter, chain, point, color):
        if not chain.guide.name:
            return

        painter.setPen(color)

        painter.drawText(
            point + QtCore.QPointF(10, -10),
            chain.guide.name.split("|")[-1]
        )

    def find_guide_at_screen_pos(self, screen_pos):
        bounds, scale, rect = self.viewport.get_current_view_data()

        if not bounds:
            return None

        closest_guide = None
        closest_distance = None

        for chain in self.viewport.preview_chains:
            if not chain.guide:
                continue

            if chain.guide.position is None:
                continue

            point = self.viewport.project_point(
                chain.guide.position,
                bounds,
                scale,
                rect
            )

            delta_x = point.x() - screen_pos.x()
            delta_y = point.y() - screen_pos.y()

            distance = (delta_x ** 2 + delta_y ** 2) ** 0.5

            if closest_distance is None or distance < closest_distance:
                closest_distance = distance
                closest_guide = chain.guide

        if closest_distance is not None and closest_distance <= self.viewport.pick_threshold:
            return closest_guide

        return None

    def pick_guide(self, screen_pos):
        guide = self.find_guide_at_screen_pos(screen_pos)

        if not guide:
            return None

        return guide.name

    def is_guide_selected(self, guide_name):
        selected_guides = getattr(
            self.viewport,
            "selected_guides",
            []
        )

        for selected_guide in selected_guides:
            if JOW_preview.nodes_match(
                guide_name,
                selected_guide
            ):
                return True

        selected_guide = getattr(
            self.viewport,
            "selected_guide",
            None
        )

        return JOW_preview.nodes_match(
            guide_name,
            selected_guide
        )