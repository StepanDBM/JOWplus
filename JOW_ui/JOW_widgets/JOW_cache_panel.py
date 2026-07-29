try:
    from PySide2 import QtWidgets
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtWidgets
    from PySide6 import QtCore

from JOW_ui.JOW_widgets.JOW_widget_utils import create_toggle_button
from JOW_ui.JOW_widgets.JOW_widget_utils import create_action_button
from JOW_ui.JOW_widgets.JOW_widget_utils import CACHE_PROMPT_BUTTON_STYLE


class JOWCachePanel(QtWidgets.QWidget):
    replace_cache_requested = QtCore.Signal()
    add_selection_requested = QtCore.Signal()
    remove_selected_requested = QtCore.Signal(list)
    clear_cache_requested = QtCore.Signal()
    cached_root_double_clicked = QtCore.Signal(str)

    lock_cache_toggled = QtCore.Signal(bool)
    apply_cached_toggled = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(JOWCachePanel, self).__init__(parent)

        self.build_ui()
        self.connect_signals()

        self.set_cache_default_style = (
            self.set_cache_from_selection_btn.styleSheet()
        )

    def build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        self.cache_header_layout = QtWidgets.QHBoxLayout()
        self.cache_header_layout.setContentsMargins(0, 0, 0, 0)
        self.cache_header_layout.setSpacing(4)

        self.cached_guide_label = QtWidgets.QLabel("Guide: None")

        self.cache_header_layout.addWidget(self.cached_guide_label)

        self.lock_selection_checkbox = create_toggle_button(
            "Lock Cache",
            checked=True,
            tooltip="Keep the cached chain locked instead of auto-changing from selection.",
            minimum_width=92
        )
        self.cache_header_layout.addWidget(self.lock_selection_checkbox)
        self.apply_cached_chain_checkbox = create_toggle_button(
            "Apply Cached",
            checked=True,
            tooltip="Apply orientation to the cached chain instead of the current Maya selection.",
            minimum_width=96
        )
        self.cache_header_layout.addWidget(self.apply_cached_chain_checkbox)
        self.set_cache_from_selection_btn = create_action_button(
            "Set Cache From Selection",
            minimum_width=145
        )
        self.cache_header_layout.addWidget(self.set_cache_from_selection_btn)
        self.add_selection_to_cache_btn = create_action_button(
            "Add Selection",
            minimum_width=95
        )
        self.cache_header_layout.addWidget(self.add_selection_to_cache_btn)
        self.remove_selected_cache_btn = create_action_button(
            "Remove Selected",
            minimum_width=110
        )
        self.remove_selected_cache_btn.setEnabled(False)
        self.cache_header_layout.addWidget(self.remove_selected_cache_btn)
        self.clear_cache_btn = create_action_button(
            "Clear Cache",
            minimum_width=85
        )
        self.cache_header_layout.addWidget(self.clear_cache_btn)
        main_layout.addLayout(self.cache_header_layout)

        self.cached_root_list = QtWidgets.QListWidget()
        self.cached_root_list.setMaximumHeight(100)

        self.cached_root_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.cached_root_list.setAlternatingRowColors(True)

        self.cached_root_list.setStyleSheet(
            """
            QListWidget {
                background-color: #181818;
                color: #dddddd;
                border: 1px solid #444444;
            }

            QListWidget::item:selected {
                background-color: #2f6f9f;
                color: #ffffff;
            }
            """
        )

        main_layout.addWidget(self.cached_root_list)

    def connect_signals(self):
        self.set_cache_from_selection_btn.clicked.connect(self.replace_cache_requested.emit)
        self.add_selection_to_cache_btn.clicked.connect(self.add_selection_requested.emit)
        self.remove_selected_cache_btn.clicked.connect(self.emit_remove_selected_requested)
        self.clear_cache_btn.clicked.connect(self.clear_cache_requested.emit)
        self.cached_root_list.itemDoubleClicked.connect(self.emit_cached_root_double_clicked)
        self.cached_root_list.itemSelectionChanged.connect(self.update_button_enabled_states)
        self.cached_root_list.currentItemChanged.connect(self.update_button_enabled_states)
        self.lock_selection_checkbox.toggled.connect(self.lock_cache_toggled.emit)
        self.apply_cached_chain_checkbox.toggled.connect(self.apply_cached_toggled.emit)

    def is_cache_locked(self):
        return self.lock_selection_checkbox.isChecked()

    def apply_cached(self):
        return self.apply_cached_chain_checkbox.isChecked()

    def selected_cached_roots(self):
        roots = []

        for item in self.cached_root_list.selectedItems():
            root = item.data(QtCore.Qt.UserRole)

            if not root:
                continue

            roots.append(root)

        return roots
    def emit_remove_selected_requested(self):
        roots = self.selected_cached_roots()

        self.remove_selected_requested.emit(roots)

    def emit_cached_root_double_clicked(self, item):
        root = item.data(
            QtCore.Qt.UserRole
        )

        if not root:
            return

        self.cached_root_double_clicked.emit(root)

    def update_button_enabled_states(self, *args):
        self.remove_selected_cache_btn.setEnabled(
            bool(self.cached_root_list.selectedItems())
        )

    def update_cache_display(
        self,
        roots,
        custom_object
    ):
        selected_roots = set(self.selected_cached_roots())

        self.cached_root_list.blockSignals(True)
        self.cached_root_list.clear()

        if roots:
            for i, root in enumerate(roots):
                short_name = root.split("|")[-1]

                item = QtWidgets.QListWidgetItem(
                    "{:02d}. {}".format(
                        i + 1,
                        short_name
                    )
                )
                item.setData(QtCore.Qt.UserRole, root)

                self.cached_root_list.addItem(item)
                if root in selected_roots:
                    item.setSelected(True)

        else:
            item = QtWidgets.QListWidgetItem("Cached Roots: None")
            item.setFlags(QtCore.Qt.NoItemFlags)
            self.cached_root_list.addItem(item)

        self.cached_root_list.blockSignals(False)

        if custom_object:
            self.cached_guide_label.setText(
                "Guide: {}".format(
                    custom_object.split("|")[-1]
                )
            )
        else:
            self.cached_guide_label.setText("Guide: None")

        self.update_button_enabled_states()

    def update_set_cache_prompt(
        self,
        should_prompt
    ):
        if should_prompt:
            self.set_cache_from_selection_btn.setStyleSheet(CACHE_PROMPT_BUTTON_STYLE)
            self.set_cache_from_selection_btn.setToolTip("Joint selected and cache is empty. Click to cache this chain.")

            return
        self.set_cache_from_selection_btn.setStyleSheet(self.set_cache_default_style)
        self.set_cache_from_selection_btn.setToolTip("Cache the currently selected joint chain.")