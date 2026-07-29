try:
    from PySide2 import QtWidgets
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtWidgets
    from PySide6 import QtCore

from JOW_ui.JOW_widgets.JOW_widget_utils import create_action_button


class JOWToolPanel(QtWidgets.QWidget):

    settings_changed = QtCore.Signal()

    create_guide_requested = QtCore.Signal()
    select_guide_requested = QtCore.Signal()
    delete_guide_requested = QtCore.Signal()
    pick_custom_object_requested = QtCore.Signal()

    AXES = ["X", "Y", "Z"]

    def __init__(self, parent=None):
        super(JOWToolPanel, self).__init__(parent)

        self._updating_axis_combos = False

        self.build_ui()
        self.connect_signals()
        self.update_axis_combo_options()

    def build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        self.configuration_layout = QtWidgets.QHBoxLayout()
        self.configuration_layout.setContentsMargins(0, 0, 0, 0)
        self.configuration_layout.setSpacing(4)

        self.configuration_layout.addWidget(
            QtWidgets.QLabel("Primary Axis")
        )

        self.primary_combo = QtWidgets.QComboBox()
        self.primary_combo.addItems(["X", "Y", "Z"])
        self.disable_combo_keyboard_focus(self.primary_combo)

        self.configuration_layout.addWidget(
            self.primary_combo
        )

        self.configuration_layout.addWidget(
            QtWidgets.QLabel("Secondary Axis")
        )

        self.secondary_combo = QtWidgets.QComboBox()
        self.secondary_combo.addItems(["X", "Y", "Z"])
        self.secondary_combo.setCurrentText("Y")
        self.disable_combo_keyboard_focus(self.secondary_combo)

        self.configuration_layout.addWidget(
            self.secondary_combo
        )

        self.configuration_layout.addWidget(
            QtWidgets.QLabel("Secondary Mode")
        )

        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems([
            "World",
            "Previous",
            "Curve Plane",
            "Custom Object"
        ])
        self.disable_combo_keyboard_focus(self.mode_combo)

        self.configuration_layout.addWidget(
            self.mode_combo
        )

        main_layout.addLayout(
            self.configuration_layout
        )

        self.guide_layout = QtWidgets.QHBoxLayout()
        self.guide_layout.setContentsMargins(0, 0, 0, 0)
        self.guide_layout.setSpacing(4)

        self.create_guide_btn = create_action_button(
            "Create Guide Locator",
            minimum_width=130
        )

        self.select_guide_btn = create_action_button(
            "Select Guide",
            minimum_width=100
        )

        self.delete_guide_btn = create_action_button(
            "Delete Guide",
            minimum_width=100
        )

        self.pick_custom_object_btn = create_action_button(
            "Pick Custom Object",
            minimum_width=130
        )

        self.guide_layout.addWidget(
            self.create_guide_btn
        )

        self.guide_layout.addWidget(
            self.select_guide_btn
        )

        self.guide_layout.addWidget(
            self.delete_guide_btn
        )

        self.guide_layout.addWidget(
            self.pick_custom_object_btn
        )

        main_layout.addLayout(
            self.guide_layout
        )

    def connect_signals(self):
        self.primary_combo.currentTextChanged.connect(
            self.on_primary_axis_changed
        )

        self.secondary_combo.currentTextChanged.connect(
            self.on_secondary_axis_changed
        )

        self.mode_combo.currentTextChanged.connect(
            self.emit_settings_changed
        )

        self.create_guide_btn.clicked.connect(
            self.create_guide_requested.emit
        )

        self.select_guide_btn.clicked.connect(
            self.select_guide_requested.emit
        )

        self.delete_guide_btn.clicked.connect(
            self.delete_guide_requested.emit
        )

        self.pick_custom_object_btn.clicked.connect(
            self.pick_custom_object_requested.emit
        )

    def disable_combo_keyboard_focus(self, combo):
        combo.setFocusPolicy(
            QtCore.Qt.NoFocus
        )

    def primary_axis(self):
        return self.primary_combo.currentText()

    def secondary_axis(self):
        return self.secondary_combo.currentText()

    def secondary_mode(self):
        return self.mode_combo.currentText()

    def emit_settings_changed(self, *args):
        self.settings_changed.emit()

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
        primary_axis = self.primary_axis()

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
            axis = axes[
                (start_index + i) % len(axes)
            ]

            if axis != forbidden_axis:
                return axis

        return "Y"

    def on_primary_axis_changed(self, value):
        if self._updating_axis_combos:
            return

        self._updating_axis_combos = True

        try:
            secondary_axis = self.secondary_axis()

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

        self.settings_changed.emit()

    def on_secondary_axis_changed(self, value):
        if self._updating_axis_combos:
            return

        self._updating_axis_combos = True

        try:
            primary_axis = self.primary_axis()

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

        self.settings_changed.emit()