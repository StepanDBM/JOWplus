try:
    from PySide2 import QtCore
    from PySide2 import QtGui
except ImportError:
    from PySide6 import QtCore
    from PySide6 import QtGui

import math

class JOWOverlayDrawer:

    def __init__(self, viewport):
        self.viewport = viewport

    ##########################################################
    # Draw
    ##########################################################

    def draw_overlay(self, painter, rect):
        lines = self.build_overlay_lines()

        if not lines:
            return

        line_height = 15
        padding = 8
        width = 150

        visible_line_count = len(lines)

        height = (visible_line_count * line_height) + (padding * 2)

        overlay_rect = QtCore.QRectF(
            8,
            8,
            width,
            height
        )

        painter.setPen(
            QtCore.Qt.NoPen
        )

        painter.setBrush(
            QtGui.QBrush(
                QtGui.QColor(0, 0, 0, 145)
            )
        )

        painter.drawRoundedRect(
            overlay_rect,
            6,
            6
        )

        x = overlay_rect.left() + padding
        y = overlay_rect.top() + padding + 11

        for line in lines:
            text = line.get("text", "")
            kind = line.get("kind", "normal")

            painter.setPen(
                self.get_color_for_kind(kind)
            )

            painter.drawText(
                QtCore.QPointF(
                    x,
                    y
                ),
                text
            )

            y += line_height

    ##########################################################
    # Build Content
    ##########################################################

    def build_overlay_lines(self):
        lines = []

        self.add_header(lines, "JOW VIEW")
        self.add_line(
            lines,
            "Mode: {}".format(
                self.viewport.secondary_mode
            )
        )
        self.add_line(
            lines,
            "Projection: {}".format(
                self.viewport.projection_mode
            )
        )
        self.add_line(
            lines,
            "Chains: {} / Joints: {}".format(
                len(self.viewport.preview_chains),
                self.get_total_joint_count()
            )
        )

        self.add_spacer(lines)

        self.add_selected_section(lines)
        self.add_orientation_change_section(lines)
        self.add_chain_section(lines)

        if self.viewport.secondary_mode == "Curve Plane":
            self.add_plane_section(lines)

        if self.viewport.secondary_mode == "Custom Object":
            self.add_guide_section(lines)

        self.add_apply_section(lines)
        self.add_warning_section(lines)

        return lines

    ##########################################################
    # Sections
    ##########################################################

    def add_selected_section(self, lines):
        self.add_header(lines, "SELECTED")

        selected_name = self.get_selected_joint_short_name()
        selected_guide = self.get_selected_guide_short_name()

        if selected_guide:
            self.add_line(
                lines,
                "Guide: {}".format(selected_guide),
                "highlight"
            )

            self.add_spacer(lines)
            return

        if not selected_name:
            self.add_line(
                lines,
                "None",
                "muted"
            )

            self.add_spacer(lines)
            return

        self.add_line(
            lines,
            selected_name,
            "highlight"
        )

        selected_index, selected_total = self.get_selected_joint_index()

        if selected_index is not None:
            self.add_line(
                lines,
                "Index: {} / {}".format(
                    selected_index + 1,
                    selected_total
                ),
                "muted"
            )

        self.add_spacer(lines)

    def add_orientation_change_section(self, lines):
        self.add_header(
            lines,
            "ORIENTATION CHANGE"
        )

        selected_delta = self.get_selected_joint_delta()

        if selected_delta is None:
            self.add_line(
                lines,
                "Selected: N/A",
                "muted"
            )
        else:
            self.add_line(
                lines,
                "Selected: {:.1f} deg".format(
                    selected_delta
                ),
                self.get_delta_kind(selected_delta)
            )

        max_delta, max_joint = self.get_max_orientation_delta()
        average_delta = self.get_average_orientation_delta()

        if max_delta is None:
            self.add_line(
                lines,
                "Max: N/A",
                "muted"
            )
        else:
            if max_joint:
                max_text = "Max: {:.1f} deg ({})".format(
                    max_delta,
                    max_joint
                )
            else:
                max_text = "Max: {:.1f} deg".format(
                    max_delta
                )

            self.add_line(
                lines,
                max_text,
                self.get_delta_kind(max_delta)
            )

        if average_delta is None:
            self.add_line(
                lines,
                "Average: N/A",
                "muted"
            )
        else:
            self.add_line(
                lines,
                "Average: {:.1f} deg".format(
                    average_delta
                ),
                self.get_delta_kind(average_delta)
            )

        self.add_spacer(lines)

    def add_chain_section(self, lines):
        self.add_header(lines, "CHAIN")

        if not self.viewport.preview_chains:
            self.add_line(lines, "No preview chain", "warning")
            self.add_spacer(lines)
            return

        first_root = self.get_first_root_short_name()

        if first_root:
            self.add_line(
                lines,
                "Root: {}".format(first_root)
            )

        if len(self.viewport.preview_chains) > 1:
            self.add_line(
                lines,
                "Multi-root preview",
                "warning"
            )

        self.add_spacer(lines)

    def add_plane_section(self, lines):
        self.add_header(lines, "PLANE")

        plane_visible = getattr(
            self.viewport,
            "show_curve_plane_surface",
            True
        )

        self.add_line(
            lines,
            "Surface: {}".format(
                "Visible" if plane_visible else "Hidden"
            ),
            "success" if plane_visible else "muted"
        )

        front_facing = self.get_curve_plane_front_facing()

        if front_facing is None:
            facing_text = "Unknown"
            facing_kind = "muted"
        elif front_facing:
            facing_text = "Front"
            facing_kind = "success"
        else:
            facing_text = "Back"
            facing_kind = "warning"

        self.add_line(
            lines,
            "Normal Side: {}".format(facing_text),
            facing_kind
        )

        self.add_line(
            lines,
            "Flip: {}".format(
                "On" if getattr(self.viewport, "flip_plane", False) else "Off"
            )
        )

        self.add_line(
            lines,
            "Average: {}".format(
                "On" if getattr(self.viewport, "average_normals", True) else "Off"
            )
        )

        self.add_line(
            lines,
            "Normal Len: {}".format(
                self.viewport.normal_length
            ),
            "muted"
        )

        self.add_spacer(lines)

    def add_guide_section(self, lines):
        self.add_header(lines, "GUIDE")

        guide_name = self.get_first_guide_short_name()

        if guide_name:
            self.add_line(
                lines,
                guide_name,
                "highlight"
            )
        else:
            self.add_line(
                lines,
                "Missing guide",
                "warning"
            )

        self.add_spacer(lines)

    def add_apply_section(self, lines):
        self.add_header(lines, "APPLY")

        self.add_line(
            lines,
            "Target: {}".format(
                getattr(self.viewport, "apply_target_label", "Unknown")
            )
        )

        self.add_line(
            lines,
            "End Joint: {}".format(
                "On" if getattr(self.viewport, "orient_end_joint", True) else "Off"
            ),
            "normal" if getattr(self.viewport, "orient_end_joint", True) else "warning"
        )

        self.add_line(
            lines,
            "Axes: {} / {}".format(
                getattr(self.viewport, "primary_axis", "?"),
                getattr(self.viewport, "secondary_axis", "?")
            ),
            "muted"
        )

        self.add_line(
            lines,
            "View Axes: C{} / P{}".format(
                "On" if getattr(self.viewport, "show_current_axes", True) else "Off",
                "On" if getattr(self.viewport, "show_preview_axes", True) else "Off"
            ),
            "muted"
        )
        self.add_line(
            lines,
            "Delta Heatmap: {}".format(
                "On" if getattr(self.viewport, "show_delta_heatmap", False) else "Off"
            ),
            "muted"
        )
        if getattr(self.viewport, "show_delta_heatmap", False):
            self.add_line(
                lines,
                "Heat: <5 G / <25 W",
                "muted"
            )

            self.add_line(
                lines,
                "      <60 O / 60+ R",
                "muted"
            )

        self.add_spacer(lines)

    def add_warning_section(self, lines):
        warnings = self.get_warnings()

        if not warnings:
            self.add_header(lines, "WARNINGS")
            self.add_line(lines, "None", "success")
            return

        self.add_header(lines, "WARNINGS")

        for warning in warnings:
            self.add_line(
                lines,
                warning,
                "warning"
            )

    ##########################################################
    # Data Helpers
    ##########################################################

    def get_total_joint_count(self):
        total = 0

        for chain in self.viewport.preview_chains:
            total += len(chain.joints)

        return total

    def get_selected_joint_short_name(self):
        selected = self.viewport.selected_joint

        if not selected:
            return None

        return selected.split("|")[-1]

    def get_selected_joint_index(self):
        selected = self.viewport.selected_joint

        if not selected:
            return None, None

        for chain in self.viewport.preview_chains:
            for i, joint in enumerate(chain.joints):
                if joint.name == selected:
                    return i, len(chain.joints)

        return None, None

    def get_selected_guide_short_name(self):
        selected = getattr(
            self.viewport,
            "selected_guide",
            None
        )

        if not selected:
            return None

        return selected.split("|")[-1]

    def get_average_orientation_delta(self):
        deltas = []

        for chain in self.viewport.preview_chains:
            for joint in chain.joints:
                delta = self.get_joint_orientation_delta(
                    joint
                )

                if delta is None:
                    continue

                deltas.append(
                    delta
                )

        if not deltas:
            return None

        return sum(deltas) / float(len(deltas))
    def get_joint_orientation_delta(self, joint):
        required = [
            joint.x_axis,
            joint.y_axis,
            joint.z_axis,
            getattr(joint, "current_x_axis", None),
            getattr(joint, "current_y_axis", None),
            getattr(joint, "current_z_axis", None)
        ]

        for value in required:
            if value is None:
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
    def get_selected_joint_delta(self):
        selected = self.viewport.selected_joint

        if not selected:
            return None

        for chain in self.viewport.preview_chains:
            for joint in chain.joints:
                if joint.name == selected:
                    return self.get_joint_orientation_delta(
                        joint
                    )

        return None
    
    def get_max_orientation_delta(self):
        max_delta = None
        max_joint = None

        for chain in self.viewport.preview_chains:
            for joint in chain.joints:
                delta = self.get_joint_orientation_delta(
                    joint
                )

                if delta is None:
                    continue

                if max_delta is None or delta > max_delta:
                    max_delta = delta
                    max_joint = joint.name.split("|")[-1]

        return max_delta, max_joint

    def get_first_root_short_name(self):
        if not self.viewport.preview_chains:
            return None

        root = self.viewport.preview_chains[0].root

        if not root:
            return None

        return root.split("|")[-1]

    def get_first_guide_short_name(self):
        for chain in self.viewport.preview_chains:
            if not chain.guide:
                continue

            if not chain.guide.name:
                continue

            return chain.guide.name.split("|")[-1]

        return None

    def get_curve_plane_front_facing(self):
        if not self.viewport.preview_chains:
            return None

        if not hasattr(self.viewport, "plane_drawer"):
            return None

        for chain in self.viewport.preview_chains:
            if chain.curve_plane_normal is None:
                continue

            return self.viewport.plane_drawer.is_curve_plane_normal_front_facing(
                chain
            )

        return None

    def get_delta_kind(self, delta):
        if delta is None:
            return "muted"

        if delta < 5.0:
            return "success"

        if delta < 25.0:
            return "normal"

        if delta < 60.0:
            return "warning"

        return "danger"

    def get_warnings(self):
        warnings = []

        if not self.viewport.preview_chains:
            warnings.append("No preview chains")
            return warnings

        selected_guide = getattr(
            self.viewport,
            "selected_guide",
            None
        )

        if not self.viewport.selected_joint and not selected_guide:
            warnings.append("No selected item")

        if len(self.viewport.preview_chains) > 1:
            warnings.append("Multiple roots cached")

        if self.viewport.secondary_mode == "Curve Plane":
            front_facing = self.get_curve_plane_front_facing()

            if front_facing is False:
                warnings.append("Viewing plane from back side")

        if self.viewport.secondary_mode == "Custom Object":
            if not self.get_first_guide_short_name():
                warnings.append("Custom guide missing")

        if not getattr(self.viewport, "orient_end_joint", True):
            warnings.append("End joint skipped")

        max_delta, max_joint = self.get_max_orientation_delta()
        if max_delta is not None:
            if max_delta >= 90.0:
                warnings.append(
                    "Large orientation change"
                )
            elif max_delta >= 45.0:
                warnings.append(
                    "Medium orientation change"
                )

        return warnings

    ##########################################################
    # Formatting Helpers
    ##########################################################

    def add_header(self, lines, text):
        lines.append(
            {
                "text": text,
                "kind": "header"
            }
        )

    def add_line(self, lines, text, kind="normal"):
        lines.append(
            {
                "text": text,
                "kind": kind
            }
        )

    def add_spacer(self, lines):
        lines.append(
            {
                "text": "",
                "kind": "normal"
            }
        )

    def get_color_for_kind(self, kind):
        if kind == "header":
            return QtGui.QColor(80, 210, 255)

        if kind == "highlight":
            return QtGui.QColor(255, 230, 120)

        if kind == "warning":
            return QtGui.QColor(255, 160, 70)

        if kind == "danger":
            return QtGui.QColor(255, 80, 80)

        if kind == "success":
            return QtGui.QColor(120, 255, 150)

        if kind == "muted":
            return QtGui.QColor(145, 145, 145)

        return QtGui.QColor(220, 220, 220)