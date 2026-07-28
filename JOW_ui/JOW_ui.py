import maya.cmds as cmds

from maya import OpenMayaUI

try:
    from shiboken2 import wrapInstance
    from PySide2 import QtWidgets
    from PySide2 import QtCore
except ImportError:
    from shiboken6 import wrapInstance
    from PySide6 import QtWidgets
    from PySide6 import QtCore

from JOW_core import JOW_core
from JOW_ui import JOW_viewport
from JOW_ui.JOW_gl import JOW_guides
from JOW_ui.JOW_gl import JOW_preview
from JOW_core.JOW_data import OrientationSettings

WINDOW_NAME = "JOW_bySDBM"

def maya_main_window():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(
        int(ptr),
        QtWidgets.QWidget
    )

class JOWWindow(QtWidgets.QDialog):

    AXES = ["X", "Y", "Z"]
    def __init__(self, parent=maya_main_window()):
        super(JOWWindow, self).__init__(parent)
        self.setWindowTitle("JOW : Joint Orient Workbench by SDBM")

        self.resize(780, 900)
        self.setMinimumSize(520, 520)
        self.setSizeGripEnabled(True)
    
        self._updating_axis_combos = False

        self.build_ui()

    def build_ui(self):
        margins = 4
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(margins, margins, margins,margins)

        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self.controls_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.controls_widget)
        layout.setContentsMargins(margins, margins, margins,margins)

        self.viewport_widget = QtWidgets.QWidget()
        viewport_layout = QtWidgets.QVBoxLayout(self.viewport_widget)
        viewport_layout.setContentsMargins(margins, margins, margins,margins)
        self.viewport_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
            )

        self.configuration_layout = QtWidgets.QHBoxLayout()


        ##########################################################
        # Primary
        ##########################################################
        self.configuration_layout.addWidget(QtWidgets.QLabel("Primary Axis"))
        self.primary_combo = QtWidgets.QComboBox()
        self.primary_combo.addItems(["X", "Y", "Z"])
        self.disable_combo_keyboard_focus(self.primary_combo)
        self.configuration_layout.addWidget(self.primary_combo)

        ##########################################################
        # Secondary
        ##########################################################
        self.configuration_layout.addWidget(QtWidgets.QLabel("Secondary Axis"))
        self.secondary_combo = QtWidgets.QComboBox()
        self.secondary_combo.addItems(["X", "Y", "Z"])
        self.disable_combo_keyboard_focus(self.secondary_combo)
        self.secondary_combo.setCurrentText("Y")

        self.configuration_layout.addWidget(self.secondary_combo)

        ##########################################################
        # Mode
        ##########################################################
        self.configuration_layout.addWidget(QtWidgets.QLabel("Secondary Mode"))
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems([
            "World",
            "Previous",
            "Curve Plane",
            "Custom Object"
        ])
        self.disable_combo_keyboard_focus(self.mode_combo)

        self.configuration_layout.addWidget(self.mode_combo)
        layout.addLayout(self.configuration_layout)

        ##########################################################
        # Guide
        ##########################################################
        guide_layout = QtWidgets.QHBoxLayout()

        create_guide_btn = QtWidgets.QPushButton("Create Guide Locator")
        create_guide_btn.clicked.connect(self.create_guide)

        select_guide_btn = QtWidgets.QPushButton("Select Guide")
        select_guide_btn.clicked.connect(self.select_guide)

        delete_guide_btn = QtWidgets.QPushButton("Delete Guide")
        delete_guide_btn.clicked.connect(self.delete_guide)

        pick_custom_object_btn = QtWidgets.QPushButton("Pick Custom Object")
        pick_custom_object_btn.clicked.connect(self.pick_custom_object)

        guide_layout.addWidget(create_guide_btn)
        guide_layout.addWidget(select_guide_btn)
        guide_layout.addWidget(delete_guide_btn)
        guide_layout.addWidget(pick_custom_object_btn)

        layout.addLayout(guide_layout)

        ##########################################################
        # Cache
        ##########################################################
        cache_layout = QtWidgets.QVBoxLayout()

        cache_header_layout = QtWidgets.QHBoxLayout()

        self.cached_guide_label = QtWidgets.QLabel("Guide: None")

        self.lock_selection_checkbox = QtWidgets.QCheckBox("Lock Cached Chain")
        self.apply_cached_chain_checkbox = QtWidgets.QCheckBox("Apply to Cached Chain")
        self.apply_cached_chain_checkbox.setChecked(True)

        refresh_selection_btn = QtWidgets.QPushButton("Set Cache From Selection")
        refresh_selection_btn.clicked.connect(self.refresh_cache_from_selection)

        clear_cache_btn = QtWidgets.QPushButton("Clear Cache")
        clear_cache_btn.clicked.connect(self.clear_cached_chain)

        cache_header_layout.addWidget(self.cached_guide_label)
        cache_header_layout.addWidget(self.lock_selection_checkbox)
        cache_header_layout.addWidget(self.apply_cached_chain_checkbox)
        cache_header_layout.addWidget(refresh_selection_btn)
        cache_header_layout.addWidget(clear_cache_btn)

        cache_layout.addLayout(cache_header_layout)

        self.cached_chain_log = QtWidgets.QTextEdit()
        self.cached_chain_log.setReadOnly(True)
        self.cached_chain_log.setMaximumHeight(90)
        self.cached_chain_log.setPlaceholderText("Cached chains will appear here...")
        self.cached_chain_log.setStyleSheet(
            "background-color: #181818; color: #dddddd; border: 1px solid #444444;"
            )

        cache_layout.addWidget(self.cached_chain_log)

        layout.addLayout(cache_layout)

        ##########################################################
        # Viewport Controls
        ##########################################################
        viewport_controls_layout = QtWidgets.QHBoxLayout()
        viewport_controls_layout.addWidget(QtWidgets.QLabel("Projection"))
        self.projection_combo = QtWidgets.QComboBox()
        self.projection_combo.addItems(["XY", "XZ", "ZY", "Orbit"])
        self.disable_combo_keyboard_focus(self.projection_combo)
        self.projection_combo.currentTextChanged.connect(self.change_projection)
        viewport_controls_layout.addWidget(self.projection_combo)

        reset_view_btn = QtWidgets.QPushButton("Reset View")
        reset_view_btn.clicked.connect(self.reset_view)

        frame_preview_btn = QtWidgets.QPushButton("Frame Preview")
        frame_preview_btn.clicked.connect(self.frame_preview)
        viewport_controls_layout.addWidget(frame_preview_btn)

        frame_selected_btn = QtWidgets.QPushButton("Frame Selected")
        frame_selected_btn.clicked.connect(self.frame_selected_joint)
        viewport_controls_layout.addWidget(frame_selected_btn)

        viewport_controls_layout.addWidget(reset_view_btn)
        layout.addLayout(viewport_controls_layout)

        ##########################################################
        # Options
        ##########################################################
        options_layout = QtWidgets.QHBoxLayout()

        self.flip_plane_checkbox = QtWidgets.QCheckBox("Flip Plane")
        self.average_normals_checkbox = QtWidgets.QCheckBox("Average Plane Normals")
        self.show_joint_names_checkbox = QtWidgets.QCheckBox("Show Joint Names")
        self.show_grid_checkbox = QtWidgets.QCheckBox("Show Grid")
        self.show_axis_gizmo_checkbox = QtWidgets.QCheckBox("Show Axis Gizmo")

        self.average_normals_checkbox.setChecked(True)
        self.show_grid_checkbox.setChecked(True)
        self.show_axis_gizmo_checkbox.setChecked(True)

        options_layout.addWidget(self.flip_plane_checkbox)
        options_layout.addWidget(self.average_normals_checkbox)
        options_layout.addWidget(self.show_joint_names_checkbox)
        options_layout.addWidget(self.show_grid_checkbox)
        options_layout.addWidget(self.show_axis_gizmo_checkbox)

        layout.addLayout(options_layout)

        ##########################################################
        # Viewport Sizes
        ##########################################################
        viewport_size_layout = QtWidgets.QHBoxLayout()

        viewport_size_layout.addWidget(QtWidgets.QLabel("Axis Length"))

        self.axis_length_spinbox = QtWidgets.QSpinBox()
        self.axis_length_spinbox.setRange(5, 200)
        self.axis_length_spinbox.setValue(28)
        viewport_size_layout.addWidget(self.axis_length_spinbox)

        viewport_size_layout.addWidget(QtWidgets.QLabel("Joint Size"))

        self.joint_size_spinbox = QtWidgets.QSpinBox()
        self.joint_size_spinbox.setRange(2, 30)
        self.joint_size_spinbox.setValue(5)
        viewport_size_layout.addWidget(self.joint_size_spinbox)

        viewport_size_layout.addWidget(QtWidgets.QLabel("Normal Length"))

        self.normal_length_spinbox = QtWidgets.QSpinBox()
        self.normal_length_spinbox.setRange(5, 300)
        self.normal_length_spinbox.setValue(60)
        viewport_size_layout.addWidget(self.normal_length_spinbox)

        layout.addLayout(viewport_size_layout)

        ##########################################################
        # Viewport
        ##########################################################
        self.viewport = JOW_viewport.JOWViewport()
        self.viewport.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        viewport_layout.addWidget(self.viewport, 1)


        self.viewport.joint_clicked.connect(self.select_joint_from_viewport)
        
        ##########################################################
        # Bottom Actions
        ##########################################################
        bottom_actions_layout = QtWidgets.QHBoxLayout()

        rebuild_preview_btn = QtWidgets.QPushButton("Rebuild Preview")
        rebuild_preview_btn.clicked.connect(self.refresh_preview)

        debug_preview_btn = QtWidgets.QPushButton("Debug Preview Data")
        debug_preview_btn.clicked.connect(self.debug_preview_data)

        apply_btn = QtWidgets.QPushButton("Apply Orientation")
        #apply_btn.setMinimumHeight(40)
        apply_btn.clicked.connect(self.apply_orientation)

        bottom_actions_layout.addWidget(rebuild_preview_btn)
        bottom_actions_layout.addWidget(debug_preview_btn)
        bottom_actions_layout.addWidget(apply_btn)

        viewport_layout.addLayout(bottom_actions_layout)

        ##########################################################
        # Warnings
        ##########################################################
        self.warning_label = QtWidgets.QLabel("Logger: ")
        self.warning_label.setStyleSheet("color: #ffcc66;")
        self.warning_label.setWordWrap(True)

        viewport_layout.addWidget(self.warning_label)


        self.main_splitter.addWidget(self.controls_widget)
        self.main_splitter.addWidget(self.viewport_widget)

        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)

        self.main_splitter.setSizes([360, 520])

        main_layout.addWidget(self.main_splitter)

        self.update_axis_combo_options()
        self.update_cache_labels()
        self.update_viewport_display_options()
        self.update_viewport_sizes()
        self.connect_signals()

    def get_settings(self):
        settings = OrientationSettings(
            primary_axis=self.primary_combo.currentText(),
            secondary_axis=self.secondary_combo.currentText(),
            secondary_mode=self.mode_combo.currentText(),
            flip_plane=self.flip_plane_checkbox.isChecked(),
            average_normals=self.average_normals_checkbox.isChecked()
        )

        if self.apply_cached_chain_checkbox.isChecked():
            settings.roots = JOW_preview.get_preview_roots()

        return settings
    
    def disable_combo_keyboard_focus(self, combo):
        combo.setFocusPolicy(QtCore.Qt.NoFocus)

    def focus_viewport(self):
        self.viewport.setFocus()

    ##########################################################
    # Cache methods
    ##########################################################

    def refresh_cache_from_selection(self):
        JOW_preview.refresh_cache_from_selection()
        self.update_cache_labels()
        self.refresh_preview()

    def clear_cached_chain(self):
        JOW_preview.clear_cache()

        self.viewport.set_preview_chains([])
        self.viewport.set_selected_joint(None)

        self.update_cache_labels()
        self.set_warning("Cache cleared.")


    def update_cache_labels(self):
        removed_count = JOW_preview.validate_cache_and_get_removed_count()

        roots = JOW_preview.get_cached_roots()
        custom_object = JOW_preview.get_cached_custom_object()

        if roots:
            lines = ["Cached Roots:"]

            for i, root in enumerate(roots):
                lines.append(
                    "{:02d}. {}".format(
                        i + 1,
                        root.split("|")[-1]
                    )
                )

            self.cached_chain_log.setPlainText("\n".join(lines))
        else:
            self.cached_chain_log.setPlainText("Cached Roots: None")

        if custom_object:
            self.cached_guide_label.setText(
                "Guide: {}".format(custom_object.split("|")[-1])
            )
        else:
            self.cached_guide_label.setText("Guide: None")

        if removed_count > 0:
            self.set_warning(
                "{} cached root(s) no longer exist and were removed.".format(removed_count)
            )

    def update_viewport_display_options(self):
        self.viewport.set_show_grid(
            self.show_grid_checkbox.isChecked()
        )

        self.viewport.set_show_axis_gizmo(
            self.show_axis_gizmo_checkbox.isChecked()
        )


    def update_viewport_sizes(self):
        self.viewport.set_axis_length(
            self.axis_length_spinbox.value()
        )

        self.viewport.set_joint_size(
            self.joint_size_spinbox.value()
        )

        self.viewport.set_normal_length(
            self.normal_length_spinbox.value()
        )


    def frame_preview(self):
        self.viewport.frame_preview()


    def frame_selected_joint(self):
        self.viewport.frame_selected_joint()

    def get_next_axis_except(self, forbidden_axis, current_axis=None):
        axes = self.AXES[:]

        if current_axis in axes:
            start_index = axes.index(current_axis) + 1
        else:
            start_index = 0

        for i in range(len(axes)):
            axis = axes[(start_index + i) % len(axes)]

            if axis != forbidden_axis:
                return axis

        return "X"


    def on_lock_selection_changed(self):
        JOW_preview.set_cache_locked(
            self.lock_selection_checkbox.isChecked()
        )

        self.update_cache_labels()
        self.refresh_preview()


    def set_combo_value_silent(self, combo, value):
        old_state = combo.blockSignals(True)
        combo.setCurrentText(value)
        combo.blockSignals(old_state)


    def set_axis_enabled(self, combo, axis, enabled):
        index = combo.findText(axis)

        if index < 0:
            return

        item = combo.model().item(index)

        if item:
            item.setEnabled(enabled)


    def update_axis_combo_options(self):
        primary_axis = self.primary_combo.currentText()

        for axis in self.AXES:
            self.set_axis_enabled(
                self.secondary_combo,
                axis,
                axis != primary_axis
            )

    def get_next_valid_secondary_axis(self, forbidden_axis, current_axis):
        axes = self.AXES[:]

        if current_axis in axes:
            start_index = axes.index(current_axis) + 1
        else:
            start_index = 0

        for i in range(len(axes)):
            axis = axes[(start_index + i) % len(axes)]

            if axis != forbidden_axis:
                return axis

        return "Y"

    def on_primary_axis_changed(self, value):
        if self._updating_axis_combos:
            return

        self._updating_axis_combos = True

        try:
            secondary_axis = self.secondary_combo.currentText()

            if secondary_axis == value:
                new_secondary_axis = self.get_next_valid_secondary_axis(
                    value,
                    secondary_axis
                )

                self.set_combo_value_silent(
                    self.secondary_combo,
                    new_secondary_axis
                )

            self.update_axis_combo_options()

        finally:
            self._updating_axis_combos = False

        self.refresh_preview()
        self.focus_viewport()

    def on_secondary_axis_changed(self, value):
        if self._updating_axis_combos:
            return

        self._updating_axis_combos = True

        try:
            primary_axis = self.primary_combo.currentText()

            if value == primary_axis:
                new_secondary_axis = self.get_next_valid_secondary_axis(
                    primary_axis,
                    value
                )

                self.set_combo_value_silent(
                    self.secondary_combo,
                    new_secondary_axis
                )

            self.update_axis_combo_options()

        finally:
            self._updating_axis_combos = False

        self.refresh_preview()
        self.focus_viewport()

    def set_warning(self, message):
        self.warning_label.setText(message)


    def clear_warning(self):
        self.warning_label.setText("")

    def connect_signals(self):
        self.primary_combo.currentTextChanged.connect(self.on_primary_axis_changed)
        self.secondary_combo.currentTextChanged.connect(self.on_secondary_axis_changed)
        self.mode_combo.currentTextChanged.connect(self.refresh_preview)

        self.flip_plane_checkbox.stateChanged.connect(self.refresh_preview)
        self.average_normals_checkbox.stateChanged.connect(self.refresh_preview)
        self.show_joint_names_checkbox.stateChanged.connect(self.refresh_preview)

        self.lock_selection_checkbox.stateChanged.connect(self.on_lock_selection_changed)
        self.apply_cached_chain_checkbox.stateChanged.connect(self.refresh_preview)

        self.show_grid_checkbox.stateChanged.connect(self.update_viewport_display_options)
        self.show_axis_gizmo_checkbox.stateChanged.connect(self.update_viewport_display_options)

        self.axis_length_spinbox.valueChanged.connect(self.update_viewport_sizes)
        self.joint_size_spinbox.valueChanged.connect(self.update_viewport_sizes)
        self.normal_length_spinbox.valueChanged.connect(self.update_viewport_sizes)

    ##########################################################
    # Secondary Axis Guide Manager
    ##########################################################

    def create_guide(self):
        guide = JOW_guides.create_guide()

        if guide:
            cmds.select(guide, r=True)
            JOW_preview.update_cached_custom_object_from_selection()

        self.update_cache_labels()
        self.refresh_preview()


    def select_guide(self):
        guide = JOW_guides.select_guide()

        if guide:
            JOW_preview.update_cached_custom_object_from_selection()
            self.set_warning("Guide selected: {}".format(guide.split("|")[-1]))

        self.update_cache_labels()
        self.refresh_preview()


    def delete_guide(self):
        JOW_guides.delete_guide()

        self.set_warning("Guide deleted.")
        self.update_cache_labels()
        self.refresh_preview()


    def pick_custom_object(self):
        custom_object = JOW_guides.get_selected_custom_object()

        if not custom_object:
            self.set_warning("Select a non-joint object to use as Custom Object guide.")
            return

        JOW_preview.update_cached_custom_object_from_selection()

        self.set_warning(
            "Custom Object picked: {}".format(
                custom_object.split("|")[-1]
            )
        )

        self.update_cache_labels()
        self.refresh_preview()



    def change_projection(self):
        self.viewport.set_projection_mode(self.projection_combo.currentText())
        self.focus_viewport()

    def reset_view(self):
        self.viewport.reset_view()

    def refresh_preview(self):
        JOW_preview.set_cache_locked(self.lock_selection_checkbox.isChecked())

        settings = self.get_settings()

        preview_chains = JOW_preview.build_preview_chains(settings)
        if settings.secondary_mode == "Custom Object" and not settings.custom_object:
            self.set_warning("Custom Object mode needs a valid non-joint guide object.")
        
        self.viewport.set_secondary_mode(settings.secondary_mode)
        self.viewport.set_show_joint_names(self.show_joint_names_checkbox.isChecked())
        self.viewport.set_preview_chains(preview_chains)

        selected = cmds.ls(sl=True, long=True) or []
        if selected:
            self.viewport.set_selected_joint(selected[0])

        self.update_cache_labels()
        if not preview_chains:
            self.set_warning("No valid cached or selected joint chains found.")
        elif settings.secondary_mode == "Custom Object" and not settings.custom_object:
            self.set_warning("Custom Object mode needs a valid non-joint guide object.")
        else:
            self.clear_warning()

        print("JOW preview refreshed:", len(preview_chains), "chain(s)")
        self.focus_viewport()

    def debug_preview_data(self):
        settings = self.get_settings()
        preview_chains = JOW_preview.build_preview_chains(settings)
        print("JOW Preview Chains:", len(preview_chains))

        for chain in preview_chains:
            print("CHAIN:", chain.root)

            for joint in chain.joints:
                print(
                    joint.name,
                    "POS:", joint.position,
                    "X:", joint.x_axis,
                    "Y:", joint.y_axis,
                    "Z:", joint.z_axis
                )

    def apply_orientation(self):
        settings = self.get_settings()

        if self.apply_cached_chain_checkbox.isChecked() and not settings.roots:
            self.set_warning("Apply To Cached Chain is enabled, but no cached chain exists.")
            return

        JOW_core.apply_orientation(settings)
        self.refresh_preview()

    ##########################################################
    # Viewport Controls on Selection Diagnostics
    ##########################################################

    def select_joint_from_viewport(self, joint_name):
        if not joint_name:
            return

        if not cmds.objExists(joint_name):
            return

        cmds.select(joint_name, r=True)
        self.viewport.set_selected_joint(joint_name)

        print("JOW viewport selected:", joint_name)