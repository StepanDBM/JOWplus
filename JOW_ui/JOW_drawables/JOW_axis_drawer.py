try:
    from PySide2 import QtCore
    from PySide2 import QtGui
except ImportError:
    from PySide6 import QtCore
    from PySide6 import QtGui


class JOWAxisDrawer:

    def __init__(self, viewport):
        self.viewport = viewport

    def is_chain_root_joint(self, joint):
        return (
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


    def get_axis_length_for_joint(self, joint):
        length = self.viewport.axis_length

        if self.is_chain_root_joint(joint):
            length *= getattr(
                self.viewport,
                "root_axis_length_multiplier",
                1.65
            )

        return length


    def get_axis_width_for_joint(self, joint):
        if self.is_chain_root_joint(joint):
            return getattr(
                self.viewport,
                "root_axis_width",
                3
            )

        return 2


    def get_axis_label_offset_for_joint(self, joint):
        if self.is_chain_root_joint(joint):
            return getattr(
                self.viewport,
                "root_axis_label_offset",
                8
            )

        return 4

    def draw_axes(self, painter, chain, bounds, scale, rect):
        if self.viewport.show_current_axes:
            self.draw_current_axes(
                painter,
                chain,
                bounds,
                scale,
                rect
            )

        if self.viewport.show_preview_axes:
            self.draw_preview_axes(
                painter,
                chain,
                bounds,
                scale,
                rect
            )
    def draw_preview_axes(self, painter, chain, bounds, scale, rect):
        for joint in chain.joints:
            origin = self.viewport.project_point(
                joint.position,
                bounds,
                scale,
                rect
            )
            show_labels = (
                joint.name in getattr(
                    self.viewport,
                    "selected_joints",
                    []
                ) or
                joint.name == self.viewport.selected_joint
            )

            axis_length = self.get_axis_length_for_joint(joint)
            axis_width = self.get_axis_width_for_joint(joint)
            label_offset = self.get_axis_label_offset_for_joint(joint)

            self.draw_axis(
                painter,
                origin,
                joint.x_axis,
                axis_length,
                QtGui.QColor(255, 80, 80),
                "X" if show_labels else None,
                width=axis_width,
                style=QtCore.Qt.SolidLine,
                label_offset=label_offset
            )

            self.draw_axis(
                painter,
                origin,
                joint.y_axis,
                axis_length,
                QtGui.QColor(80, 255, 80),
                "Y" if show_labels else None,
                width=axis_width,
                style=QtCore.Qt.SolidLine,
                label_offset=label_offset
            )

            self.draw_axis(
                painter,
                origin,
                joint.z_axis,
                axis_length,
                QtGui.QColor(80, 140, 255),
                "Z" if show_labels else None,
                width=axis_width,
                style=QtCore.Qt.SolidLine,
                label_offset=label_offset
            )
    def draw_current_axes(self, painter, chain, bounds, scale, rect):
        for joint in chain.joints:
            if joint.current_position is None:
                continue

            origin = self.viewport.project_point(
                joint.current_position,
                bounds,
                scale,
                rect
            )
            length = self.get_axis_length_for_joint(joint)
            width = self.get_axis_width_for_joint(joint)

            self.draw_axis(
                painter,
                origin,
                joint.current_x_axis,
                length,
                QtGui.QColor(160, 70, 70, 150),
                None,
                width=width,
                style=QtCore.Qt.DashLine
            )

            self.draw_axis(
                painter,
                origin,
                joint.current_y_axis,
                length,
                QtGui.QColor(70, 160, 70, 150),
                None,
                width=width,
                style=QtCore.Qt.DashLine
            )

            self.draw_axis(
                painter,
                origin,
                joint.current_z_axis,
                length,
                QtGui.QColor(70, 100, 180, 150),
                None,
                width=width,
                style=QtCore.Qt.DashLine
            )

    def draw_axis(self, painter, origin, axis, length, color, label=None, width=2, style=QtCore.Qt.SolidLine, label_offset=4):
        if axis is None:
            return

        axis_a, axis_b = self.viewport.project_axis(axis)
        pen = QtGui.QPen(color, width)
        pen.setStyle(style)

        painter.setPen(pen)
        end = QtCore.QPointF(
            origin.x() + axis_a * length,
            origin.y() - axis_b * length
        )
        painter.drawLine(origin, end)

        if label:
            painter.setPen(color)
            painter.drawText(
                end + QtCore.QPointF(
                    label_offset,
                    -label_offset
                ),
                label
            )

    def draw_axis_gizmo(self, painter, rect):
        if not self.viewport.show_axis_gizmo:
            return

        origin = QtCore.QPointF(
            rect.right() - 70,
            rect.bottom() - 55
        )

        length = 32

        axes = [
            ("X", self.viewport.vector_from_components(1, 0, 0), QtGui.QColor(255, 80, 80)),
            ("Y", self.viewport.vector_from_components(0, 1, 0), QtGui.QColor(80, 255, 80)),
            ("Z", self.viewport.vector_from_components(0, 0, 1), QtGui.QColor(80, 140, 255))
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

    def project_gizmo_axis(self, axis, label):
        axis_a, axis_b = self.viewport.project_axis(axis)

        if self.viewport.projection_mode == "ZY" and label == "Z":
            axis_a *= -1

        return axis_a, axis_b