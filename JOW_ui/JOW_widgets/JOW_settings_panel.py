try:
    from PySide2 import QtWidgets
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtWidgets
    from PySide6 import QtCore

from JOW_ui.JOW_widgets.JOW_widget_utils import create_toggle_button
from JOW_ui.JOW_widgets.JOW_widget_utils import create_action_button
from JOW_ui.JOW_widgets.JOW_widget_utils import create_toggle_grid_layout


class JOWSettingsPanel(QtWidgets.QWidget):

    display_options_changed = QtCore.Signal()
    preview_settings_changed = QtCore.Signal()
    sizes_changed = QtCore.Signal()

    live_sync_toggled = QtCore.Signal(bool)
    projection_changed = QtCore.Signal(str)

    frame_preview_requested = QtCore.Signal()
    frame_selected_requested = QtCore.Signal()
    reset_view_requested = QtCore.Signal()

    native_rotation_axes_toggled = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(JOWSettingsPanel, self).__init__(parent)

        self.build_ui()
        self.connect_signals()

    def build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        self.viewport_controls_layout = QtWidgets.QHBoxLayout()
        self.viewport_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.viewport_controls_layout.setSpacing(4)

        self.show_overlay_checkbox = create_toggle_button(
            "Overlay",
            checked=True,
            tooltip="Show or hide the viewport overlay.",
            minimum_width=76
        )

        self.show_delta_heatmap_checkbox = create_toggle_button(
            "Delta Heat",
            checked=False,
            tooltip="Show orientation delta heatmap rings on all joints.",
            minimum_width=86
        )

        self.live_sync_checkbox = create_toggle_button(
            "Live Sync",
            checked=True,
            tooltip="Automatically refresh the JOW viewport when cached joints or the cached guide move in Maya.",
            minimum_width=82
        )

        self.viewport_controls_layout.addWidget(self.show_overlay_checkbox)
        self.viewport_controls_layout.addWidget(self.show_delta_heatmap_checkbox)
        self.viewport_controls_layout.addWidget(self.live_sync_checkbox)
        self.viewport_controls_layout.addWidget(QtWidgets.QLabel("Projection"))

        self.projection_combo = QtWidgets.QComboBox()
        self.projection_combo.addItems(["Orbit", "XY", "XZ", "ZY"])
        self.projection_combo.setFocusPolicy(QtCore.Qt.NoFocus)

        self.viewport_controls_layout.addWidget(self.projection_combo)

        self.frame_preview_btn = create_action_button("Frame Preview", minimum_width=100)
        self.frame_selected_btn = create_action_button("Frame Selected", minimum_width=105)
        self.reset_view_btn = create_action_button("Reset View", minimum_width=90)

        self.viewport_controls_layout.addWidget(self.frame_preview_btn)
        self.viewport_controls_layout.addWidget(self.frame_selected_btn)
        self.viewport_controls_layout.addWidget(self.reset_view_btn)

        main_layout.addLayout(self.viewport_controls_layout)

        self.options_layout = create_toggle_grid_layout()

        self.show_plane_checkbox = create_toggle_button(
            "Plane Viz",
            checked=True,
            tooltip="Show or hide the curve plane surface."
        )

        self.flip_plane_checkbox = create_toggle_button(
            "Flip Plane",
            checked=False,
            tooltip="Flip the computed curve plane normal."
        )

        self.average_normals_checkbox = create_toggle_button(
            "Avg Normals",
            checked=True,
            tooltip="Average all valid curve-plane triplet normals."
        )

        self.orient_end_joint_checkbox = create_toggle_button(
            "End Joint",
            checked=True,
            tooltip="Include the end joint in orientation preview and apply."
        )

        self.show_joint_names_checkbox = create_toggle_button(
            "Jnt Names",
            checked=False,
            tooltip="Show joint names in the viewport."
        )
        self.native_rotation_axes_checkbox = create_toggle_button(
            "Maya LRA",
            checked=False,
            tooltip="Show or hide Maya native Local Rotation Axes on cached joints only."
        )

        self.show_grid_checkbox = create_toggle_button(
            "Grid Viz",
            checked=True,
            tooltip="Show or hide the projected world grid."
        )

        self.show_axis_gizmo_checkbox = create_toggle_button(
            "Axis Gizmo",
            checked=True,
            tooltip="Show or hide the mini viewport axis gizmo."
        )

        self.options_layout.addWidget(self.show_plane_checkbox, 0, 0)
        self.options_layout.addWidget(self.flip_plane_checkbox, 0, 1)
        self.options_layout.addWidget(self.average_normals_checkbox, 0, 2)
        self.options_layout.addWidget(self.show_grid_checkbox, 0, 3)
        self.options_layout.addWidget(self.orient_end_joint_checkbox, 1, 0)
        self.options_layout.addWidget(self.show_joint_names_checkbox, 1, 1)
        self.options_layout.addWidget(self.native_rotation_axes_checkbox, 1, 2)
        self.options_layout.addWidget(self.show_axis_gizmo_checkbox, 1, 3)
        main_layout.addLayout(self.options_layout)

        self.viewport_size_layout = QtWidgets.QHBoxLayout()
        self.viewport_size_layout.setContentsMargins(0, 0, 0, 0)
        self.viewport_size_layout.setSpacing(4)

        self.show_3d_joints_checkbox = create_toggle_button(
            "3D Joints",
            checked=True,
            tooltip="Draw pyramid-style projected joint bones.",
            minimum_width=84
        )

        self.show_current_axes_checkbox = create_toggle_button(
            "Current Axes",
            checked=True,
            tooltip="Draw current Maya joint axes as ghost axes.",
            minimum_width=100
        )

        self.show_preview_axes_checkbox = create_toggle_button(
            "Preview Axes",
            checked=True,
            tooltip="Draw proposed JOW orientation axes.",
            minimum_width=100
        )

        self.viewport_size_layout.addWidget(self.show_3d_joints_checkbox)
        self.viewport_size_layout.addWidget(self.show_current_axes_checkbox)
        self.viewport_size_layout.addWidget(self.show_preview_axes_checkbox)
        self.viewport_size_layout.addWidget(QtWidgets.QLabel("Axis Length"))

        self.axis_length_spinbox = QtWidgets.QSpinBox()
        self.axis_length_spinbox.setRange(5, 200)
        self.axis_length_spinbox.setValue(28)

        self.viewport_size_layout.addWidget(self.axis_length_spinbox)

        self.viewport_size_layout.addWidget(QtWidgets.QLabel("Joint Size"))

        self.joint_size_spinbox = QtWidgets.QSpinBox()
        self.joint_size_spinbox.setRange(2, 30)
        self.joint_size_spinbox.setValue(5)

        self.viewport_size_layout.addWidget(self.joint_size_spinbox)

        self.viewport_size_layout.addWidget(QtWidgets.QLabel("Normal Length"))

        self.normal_length_spinbox = QtWidgets.QSpinBox()
        self.normal_length_spinbox.setRange(5, 300)
        self.normal_length_spinbox.setValue(60)

        self.viewport_size_layout.addWidget(self.normal_length_spinbox)

        main_layout.addLayout(self.viewport_size_layout)

    def connect_signals(self):
        self.show_overlay_checkbox.toggled.connect(self.emit_display_options_changed)
        self.show_delta_heatmap_checkbox.toggled.connect(self.emit_display_options_changed)
        self.show_grid_checkbox.toggled.connect(self.emit_display_options_changed)
        self.show_axis_gizmo_checkbox.toggled.connect(self.emit_display_options_changed)
        self.show_plane_checkbox.toggled.connect(self.emit_display_options_changed)
        self.show_3d_joints_checkbox.toggled.connect(self.emit_display_options_changed)
        self.show_current_axes_checkbox.toggled.connect(self.emit_display_options_changed)
        self.show_preview_axes_checkbox.toggled.connect(self.emit_display_options_changed)

        self.flip_plane_checkbox.toggled.connect(self.emit_preview_settings_changed)
        self.average_normals_checkbox.toggled.connect(self.emit_preview_settings_changed)
        self.orient_end_joint_checkbox.toggled.connect(self.emit_preview_settings_changed)
        self.show_joint_names_checkbox.toggled.connect(self.emit_preview_settings_changed)

        self.live_sync_checkbox.toggled.connect(self.live_sync_toggled.emit)
        self.projection_combo.currentTextChanged.connect(self.projection_changed.emit)

        self.native_rotation_axes_checkbox.toggled.connect(self.native_rotation_axes_toggled.emit)

        self.frame_preview_btn.clicked.connect(self.frame_preview_requested.emit)
        self.frame_selected_btn.clicked.connect(self.frame_selected_requested.emit)
        self.reset_view_btn.clicked.connect(self.reset_view_requested.emit)

        self.axis_length_spinbox.valueChanged.connect(self.emit_sizes_changed)
        self.joint_size_spinbox.valueChanged.connect(self.emit_sizes_changed)
        self.normal_length_spinbox.valueChanged.connect(self.emit_sizes_changed)

    def emit_display_options_changed(self, *args):
        self.display_options_changed.emit()
    def emit_preview_settings_changed(self, *args):
        self.preview_settings_changed.emit()
    def emit_sizes_changed(self, *args):
        self.sizes_changed.emit()
    def show_grid(self):
        return self.show_grid_checkbox.isChecked()
    def show_axis_gizmo(self):
        return self.show_axis_gizmo_checkbox.isChecked()
    def show_3d_joints(self):
        return self.show_3d_joints_checkbox.isChecked()
    def show_plane(self):
        return self.show_plane_checkbox.isChecked()
    def show_current_axes(self):
        return self.show_current_axes_checkbox.isChecked()
    def show_preview_axes(self):
        return self.show_preview_axes_checkbox.isChecked()
    def show_overlay(self):
        return self.show_overlay_checkbox.isChecked()
    def show_delta_heatmap(self):
        return self.show_delta_heatmap_checkbox.isChecked()
    def show_joint_names(self):
        return self.show_joint_names_checkbox.isChecked()
    def flip_plane(self):
        return self.flip_plane_checkbox.isChecked()
    def average_normals(self):
        return self.average_normals_checkbox.isChecked()
    def orient_end_joint(self):
        return self.orient_end_joint_checkbox.isChecked()
    def live_sync_enabled(self):
        return self.live_sync_checkbox.isChecked()
    def native_rotation_axes_enabled(self):
        return self.native_rotation_axes_checkbox.isChecked()
    def projection_mode(self):
        return self.projection_combo.currentText()
    def axis_length(self):
        return self.axis_length_spinbox.value()
    def joint_size(self):
        return self.joint_size_spinbox.value()
    def normal_length(self):
        return self.normal_length_spinbox.value()