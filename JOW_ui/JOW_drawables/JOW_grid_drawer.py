try:
    from PySide2 import QtGui
except ImportError:
    from PySide6 import QtGui


import math as py_math


class JOWGridDrawer:

    def __init__(self, viewport):
        self.viewport = viewport

    ##########################################################
    # Grid Plane
    ##########################################################

    def get_grid_plane(self):
        if self.viewport.projection_mode == "XY":
            return "XY"

        if self.viewport.projection_mode == "XZ":
            return "XZ"

        if self.viewport.projection_mode == "ZY":
            return "ZY"

        if self.viewport.projection_mode == "Orbit":
            return "XZ"

        return "XZ"


    def make_grid_point(self, u, v):
        grid_plane = self.get_grid_plane()

        if grid_plane == "XY":
            return self.viewport.vector_from_components(
                u,
                v,
                0
            )

        if grid_plane == "XZ":
            return self.viewport.vector_from_components(
                u,
                0,
                v
            )

        if grid_plane == "ZY":
            return self.viewport.vector_from_components(
                0,
                v,
                u
            )

        return self.viewport.vector_from_components(
            u,
            0,
            v
        )


    def get_grid_center_uv(self):
        points = self.viewport.collect_points()

        if not points:
            return 0.0, 0.0

        grid_plane = self.get_grid_plane()

        if grid_plane == "XY":
            values = [
                (p.x, p.y)
                for p in points
            ]

        elif grid_plane == "XZ":
            values = [
                (p.x, p.z)
                for p in points
            ]

        elif grid_plane == "ZY":
            values = [
                (p.z, p.y)
                for p in points
            ]

        else:
            values = [
                (p.x, p.z)
                for p in points
            ]

        min_u = min(v[0] for v in values)
        max_u = max(v[0] for v in values)

        min_v = min(v[1] for v in values)
        max_v = max(v[1] for v in values)

        center_u = (min_u + max_u) * 0.5
        center_v = (min_v + max_v) * 0.5

        return center_u, center_v


    def project_grid_point(self, u, v, rect, scale):
        point = self.make_grid_point(
            u,
            v
        )

        return self.viewport.project_point(
            point,
            None,
            scale,
            rect
        )

    ##########################################################
    # Grid Scale
    ##########################################################

    def get_grid_size(self, scale):
        if scale <= 0:
            return 1.0

        target_pixels = 45.0
        target_world_size = target_pixels / scale

        if target_world_size <= 0:
            return 1.0

        magnitude = 10 ** py_math.floor(
            py_math.log10(target_world_size)
        )

        for multiplier in [1, 2, 5, 10]:

            grid_size = magnitude * multiplier

            if grid_size >= target_world_size:
                return grid_size

        return magnitude * 10

    ##########################################################
    # Grid Drawing
    ##########################################################

    def draw_grid(self, painter, rect):
        if not self.viewport.show_grid:
            return

        scale = self.viewport.get_scale(
            None,
            rect
        )

        if scale <= 0:
            return

        grid_size = self.get_grid_size(
            scale
        )

        center_u, center_v = self.get_grid_center_uv()

        visible_world_size = max(
            rect.width(),
            rect.height()
        ) / scale

        extent = max(
            visible_world_size * 1.5,
            grid_size * 20
        )

        min_u = center_u - extent
        max_u = center_u + extent

        min_v = center_v - extent
        max_v = center_v + extent

        start_u = py_math.floor(
            min_u / grid_size
        ) * grid_size

        start_v = py_math.floor(
            min_v / grid_size
        ) * grid_size

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(45, 45, 45),
                1
            )
        )

        u = start_u

        while u <= max_u:

            point_a = self.project_grid_point(
                u,
                min_v,
                rect,
                scale
            )

            point_b = self.project_grid_point(
                u,
                max_v,
                rect,
                scale
            )

            painter.drawLine(
                point_a,
                point_b
            )

            u += grid_size

        v = start_v

        while v <= max_v:

            point_a = self.project_grid_point(
                min_u,
                v,
                rect,
                scale
            )

            point_b = self.project_grid_point(
                max_u,
                v,
                rect,
                scale
            )

            painter.drawLine(
                point_a,
                point_b
            )

            v += grid_size

        self.draw_grid_origin_axes(
            painter,
            rect,
            scale,
            min_u,
            max_u,
            min_v,
            max_v
        )


    def draw_grid_origin_axes(
        self,
        painter,
        rect,
        scale,
        min_u,
        max_u,
        min_v,
        max_v
    ):
        grid_plane = self.get_grid_plane()

        if grid_plane == "XY":

            horizontal_color = QtGui.QColor(255, 80, 80)
            vertical_color = QtGui.QColor(80, 255, 80)

        elif grid_plane == "XZ":

            horizontal_color = QtGui.QColor(255, 80, 80)
            vertical_color = QtGui.QColor(80, 140, 255)

        elif grid_plane == "ZY":

            horizontal_color = QtGui.QColor(80, 140, 255)
            vertical_color = QtGui.QColor(80, 255, 80)

        else:

            horizontal_color = QtGui.QColor(255, 80, 80)
            vertical_color = QtGui.QColor(80, 140, 255)

        line_width = 1

        if min_v <= 0 <= max_v:

            painter.setPen(
                QtGui.QPen(
                    horizontal_color,
                    line_width
                )
            )

            point_a = self.project_grid_point(
                min_u,
                0,
                rect,
                scale
            )

            point_b = self.project_grid_point(
                max_u,
                0,
                rect,
                scale
            )

            painter.drawLine(
                point_a,
                point_b
            )

        if min_u <= 0 <= max_u:

            painter.setPen(
                QtGui.QPen(
                    vertical_color,
                    line_width
                )
            )

            point_a = self.project_grid_point(
                0,
                min_v,
                rect,
                scale
            )

            point_b = self.project_grid_point(
                0,
                max_v,
                rect,
                scale
            )

            painter.drawLine(
                point_a,
                point_b
            )