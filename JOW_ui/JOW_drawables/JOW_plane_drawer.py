try:
    from PySide2 import QtCore
    from PySide2 import QtGui
except ImportError:
    from PySide6 import QtCore
    from PySide6 import QtGui


class JOWPlaneDrawer:

    def __init__(self, viewport):
        self.viewport = viewport

    ##########################################################
    # Facing Logic
    ##########################################################
    def get_vector_view_depth(self, vector):
        if self.viewport.projection_mode == "XY":
            return vector.z

        if self.viewport.projection_mode == "XZ":
            return vector.y

        if self.viewport.projection_mode == "ZY":
            return vector.x

        if self.viewport.projection_mode == "Orbit":
            x, y, z = self.viewport.rotate_vector(vector)
            return z

        return vector.z


    def is_curve_plane_normal_front_facing(self, chain):
        if chain.curve_plane_normal is None:
            return True

        depth = self.get_vector_view_depth(
            chain.curve_plane_normal
        )

        return depth >= 0.0
    
    ##########################################################
    # Curve Plane Surface
    ##########################################################
    def draw_curve_plane_surface(self, painter, chain, bounds, scale, rect):
        if not self.viewport.show_curve_plane_surface:
            return        
        if self.viewport.secondary_mode != "Curve Plane":
            return        
        if chain.curve_plane_center is None:
            return
        if chain.curve_plane_normal is None:
            return
        if not chain.joints:
            return
  
        corners = self.get_curve_plane_corners(chain)

        if not corners:
            return

        projected_points = [
            self.viewport.project_point(
                point,
                bounds,
                scale,
                rect
            )
            for point in corners
        ]

        polygon = QtGui.QPolygonF(
            projected_points
        )

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(0, 190, 255, 160),
                1
            )
        )

        painter.setBrush(
            QtGui.QBrush(
                QtGui.QColor(0, 190, 255, 35)
            )
        )

        painter.drawPolygon(polygon)

    def get_curve_plane_corners(self, chain):
        center = chain.curve_plane_center
        normal = chain.curve_plane_normal

        if center is None:
            return None
        if normal is None:
            return None

        normal = normal.normal()
        basis_a, basis_b = self.get_plane_basis(normal)

        if basis_a is None or basis_b is None:
            return None

        half_width, half_height = self.get_chain_plane_size(
            chain,
            center,
            basis_a,
            basis_b
        )

        corner_a = center + (basis_a * half_width) + (basis_b * half_height)
        corner_b = center - (basis_a * half_width) + (basis_b * half_height)
        corner_c = center - (basis_a * half_width) - (basis_b * half_height)
        corner_d = center + (basis_a * half_width) - (basis_b * half_height)

        return [
            corner_a,
            corner_b,
            corner_c,
            corner_d
        ]

    def make_vector_like(self, source_vector, x, y, z):
        return source_vector.__class__(x, y, z)


    def get_plane_basis(self, normal):
        fallback = self.make_vector_like(
            normal,
            0,
            1,
            0
        )

        if abs(normal * fallback) > 0.95:
            fallback = self.make_vector_like(
                normal,
                1,
                0,
                0
            )

        basis_a = normal ^ fallback

        if basis_a.length() < 0.0001:
            return None, None

        basis_a = basis_a.normal()
        basis_b = normal ^ basis_a

        if basis_b.length() < 0.0001:
            return None, None

        basis_b = basis_b.normal()

        return basis_a, basis_b

    def get_chain_plane_size(
        self,
        chain,
        center,
        basis_a,
        basis_b
    ):
        values_a = []
        values_b = []

        for joint in chain.joints:
            if joint.position is None:
                continue

            offset = joint.position - center

            values_a.append(offset * basis_a)

            values_b.append(offset * basis_b)

        if not values_a or not values_b:
            return 1.0, 1.0

        min_a = min(values_a)
        max_a = max(values_a)

        min_b = min(values_b)
        max_b = max(values_b)

        width = max(max_a - min_a, 0.001)
        height = max(max_b - min_b, 0.001)

        padding = 1.25

        half_width = max(width * 0.5 * padding, 0.5)
        half_height = max(height * 0.5 * padding, 0.5)

        return half_width, half_height

    ##########################################################
    # Curve Plane Normal
    ##########################################################
    def get_line_intersection_t(
        self,
        line_a,
        line_b,
        edge_a,
        edge_b
    ):
        p_x = line_a.x()
        p_y = line_a.y()

        r_x = line_b.x() - line_a.x()
        r_y = line_b.y() - line_a.y()

        q_x = edge_a.x()
        q_y = edge_a.y()

        s_x = edge_b.x() - edge_a.x()
        s_y = edge_b.y() - edge_a.y()

        denominator = self.cross_2d(
            r_x,
            r_y,
            s_x,
            s_y
        )

        if abs(denominator) < 0.000001:
            return None

        q_minus_p_x = q_x - p_x
        q_minus_p_y = q_y - p_y

        t = self.cross_2d(
            q_minus_p_x,
            q_minus_p_y,
            s_x,
            s_y
        ) / denominator

        u = self.cross_2d(
            q_minus_p_x,
            q_minus_p_y,
            r_x,
            r_y
        ) / denominator

        if t < 0.0 or t > 1.0:
            return None
        if u < 0.0 or u > 1.0:
            return None

        return t


    def cross_2d(self, a_x, a_y, b_x, b_y):
        return (a_x * b_y) - (a_y * b_x)


    def point_on_screen_line(self, point_a, point_b, t):
        return QtCore.QPointF(
            point_a.x() + ((point_b.x() - point_a.x()) * t),
            point_a.y() + ((point_b.y() - point_a.y()) * t)
        )
    
    def get_normal_world_length(self, scale):
        if scale <= 0.0001:
            return 1.0

        return max(
            self.viewport.normal_length / scale,
            0.001
        )
    
    def get_clipped_normal_ray_segments(
        self,
        center_screen,
        front_screen,
        polygon_points
    ):
        t_values = [0.0, 1.0]

        count = len(polygon_points)

        for i in range(count):
            edge_a = polygon_points[i]
            edge_b = polygon_points[(i + 1) % count]

            t = self.get_line_intersection_t(
                center_screen,
                front_screen,
                edge_a,
                edge_b
            )

            if t is None:
                continue

            if 0.0 <= t <= 1.0:
                t_values.append(t)

        t_values = sorted(
            list(
                set(
                    [
                        round(t, 6)
                        for t in t_values
                    ]
                )
            )
        )

        polygon = QtGui.QPolygonF(polygon_points)

        segments = []

        for i in range(len(t_values) - 1):
            t_a = t_values[i]
            t_b = t_values[i + 1]

            if abs(t_b - t_a) < 0.00001:
                continue

            mid_t = (t_a + t_b) * 0.5

            point_a = self.point_on_screen_line(
                center_screen,
                front_screen,
                t_a
            )

            point_b = self.point_on_screen_line(
                center_screen,
                front_screen,
                t_b
            )

            mid_point = self.point_on_screen_line(
                center_screen,
                front_screen,
                mid_t
            )

            inside_plane = polygon.containsPoint(
                mid_point,
                QtCore.Qt.OddEvenFill
            )

            segments.append(
                (
                    point_a,
                    point_b,
                    inside_plane,
                    t_a,
                    t_b
                )
            )

        return segments
    
    def get_projected_curve_plane_polygon(
        self,
        chain,
        bounds,
        scale,
        rect
    ):
        corners = self.get_curve_plane_corners(chain)

        if not corners:
            return None

        return [
            self.viewport.project_point(
                point,
                bounds,
                scale,
                rect
            )
            for point in corners
        ]

    def draw_normal_segment(
        self,
        painter,
        point_a,
        point_b,
        hidden=False
    ):
        if hidden:
            color = QtGui.QColor(80, 70, 25, 130)
            width = 2
            style = QtCore.Qt.DashLine
        else:
            color = QtGui.QColor(255, 230, 80, 255)
            width = 3
            style = QtCore.Qt.SolidLine

        pen = QtGui.QPen(color, width)
        pen.setStyle(style)
        painter.setPen(pen)
        painter.drawLine(point_a, point_b)

    def draw_normal_tip(
        self,
        painter,
        point,
        hidden=False
    ):
        if hidden:
            color = QtGui.QColor(80, 70, 25, 130)
            outline_color = QtGui.QColor(80, 70, 25, 150)
            radius = 3
        else:
            color = QtGui.QColor(255, 230, 80, 255)
            outline_color = QtGui.QColor(255, 245, 150, 255)
            radius = 4

        painter.setPen(
            QtGui.QPen(
                outline_color,
                2
            )
        )

        painter.setBrush(QtGui.QBrush(color))

        painter.drawEllipse(
            point,
            radius,
            radius
        )

    def draw_curve_plane_normal_hidden(self, painter, chain, bounds, scale, rect):
        self.draw_curve_plane_normal_clipped(
            painter,
            chain,
            bounds,
            scale,
            rect,
            draw_hidden=True
        )


    def draw_curve_plane_normal_visible(self, painter, chain, bounds, scale, rect):
        self.draw_curve_plane_normal_clipped(
            painter,
            chain,
            bounds,
            scale,
            rect,
            draw_hidden=False
        )

    def draw_curve_plane_normal_clipped(
        self,
        painter,
        chain,
        bounds,
        scale,
        rect,
        draw_hidden=False
    ):
        if self.viewport.secondary_mode != "Curve Plane":
            return
        if chain.curve_plane_center is None:
            return
        if chain.curve_plane_normal is None:
            return
        if chain.curve_plane_normal.length() < 0.0001:
            return

        polygon_points = self.get_projected_curve_plane_polygon(
            chain,
            bounds,
            scale,
            rect
        )

        if not polygon_points:
            return

        front_facing = self.is_curve_plane_normal_front_facing(chain)
        normal = chain.curve_plane_normal.normal()
        world_length = self.get_normal_world_length(scale)

        center_world = chain.curve_plane_center
        front_world = center_world + (normal * world_length)

        center_screen = self.viewport.project_point(
            center_world,
            bounds,
            scale,
            rect
        )

        front_screen = self.viewport.project_point(
            front_world,
            bounds,
            scale,
            rect
        )

        segments = self.get_clipped_normal_ray_segments(
            center_screen,
            front_screen,
            polygon_points
        )

        for segment in segments:
            point_a, point_b, inside_plane, t_a, t_b = segment

            # Front-facing means the normal is coming toward the viewer.
            # In that case, the whole +normal ray should be visible on top.
            if front_facing:
                is_hidden_segment = False

            # Back-facing means the +normal ray is behind the plane.
            # Only the part visually inside the plane polygon gets hidden.
            else:
                is_hidden_segment = inside_plane

            if draw_hidden != is_hidden_segment:
                continue

            self.draw_normal_segment(
                painter,
                point_a,
                point_b,
                hidden=is_hidden_segment
            )

        self.draw_normal_tip_for_pass(
            painter,
            front_screen,
            polygon_points,
            front_facing,
            draw_hidden
        )

    def draw_normal_tip_for_pass(
        self,
        painter,
        tip_point,
        polygon_points,
        front_facing,
        draw_hidden
    ):
        polygon = QtGui.QPolygonF(polygon_points)
        tip_inside_plane = polygon.containsPoint(
            tip_point,
            QtCore.Qt.OddEvenFill
        )

        if front_facing:
            tip_is_hidden = False
        else:
            tip_is_hidden = tip_inside_plane

        if draw_hidden != tip_is_hidden:
            return

        self.draw_normal_tip(
            painter,
            tip_point,
            hidden=tip_is_hidden
        )


    ##########################################################
    # Previous Mode Normals
    ##########################################################
    def draw_previous_normals(self, painter, chain, bounds, scale, rect):
        if self.viewport.secondary_mode != "Previous":
            return

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(255, 180, 60),
                2
            )
        )

        length = self.viewport.normal_length
        for previous_normal in chain.previous_normals:

            if previous_normal.position is None:
                continue

            if previous_normal.normal is None:
                continue

            origin = self.viewport.project_point(
                previous_normal.position,
                bounds,
                scale,
                rect
            )

            axis_a, axis_b = self.viewport.project_axis(
                previous_normal.normal
            )

            end = QtCore.QPointF(
                origin.x() + axis_a * length,
                origin.y() - axis_b * length
            )

            painter.drawLine(
                origin,
                end
            )

            painter.setBrush(
                QtGui.QBrush(
                    QtGui.QColor(255, 180, 60)
                )
            )

            painter.drawEllipse(
                end,
                3,
                3
            )