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

from JOW_core.JOW_utils.JOW_undo import undo_chunk

from JOW_core.JOW_maya import JOW_maya_nodes
from JOW_core.JOW_maya import JOW_maya_joints
from JOW_core.JOW_maya import JOW_maya_selection
from JOW_core.JOW_maya import JOW_maya_transforms
from JOW_core.JOW_maya import JOW_maya_display
from JOW_core.JOW_maya import JOW_maya_script_jobs

from JOW_ui.JOW_widgets.JOW_tool_panel import JOWToolPanel
from JOW_ui.JOW_widgets.JOW_cache_panel import JOWCachePanel
from JOW_ui.JOW_widgets.JOW_settings_panel import JOWSettingsPanel
from JOW_ui.JOW_widgets.JOW_widget_utils import create_action_button


WINDOW_NAME = "JOW_bySDBM"


def maya_main_window():
    ptr = OpenMayaUI.MQtUtil.mainWindow()

    return wrapInstance(
        int(ptr),
        QtWidgets.QWidget
    )


class JOWWindow(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(JOWWindow, self).__init__(parent)

        self.setWindowTitle("JOW : Joint Orient Workbench by SDBM")
        self.resize(780, 900)
        self.setMinimumSize(520, 520)
        self.setSizeGripEnabled(True)

        self.selection_script_job = None

        self.live_sync_timer = None
        self.live_sync_snapshot = {}
        self.live_sync_interval_ms = 50
        self.live_sync_tolerance = 0.00001
        self._live_sync_refreshing = False

        self.native_rotation_axis_nodes = set()

        self._syncing_selection_from_viewport = False

        self.ui_settings = QtCore.QSettings(
            "SDBM",
            "JOW_SDBM"
        )

        self.build_ui()
        self.restore_ui_state()
        self.connect_signals()

        self.create_selection_script_job()
        self.create_live_sync_timer()

        self.refresh_cache_panel()
        self.update_viewport_display_options()
        self.update_viewport_sizes()

        self.set_cached_native_rotation_axes_visibility(self.tool_panel.native_rotation_axes_enabled())

    ##########################################################
    # Build UI
    ##########################################################

    def settings_bool(self, key, default=False):
        value = self.ui_settings.value(key, default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in [
                "true",
                "1",
                "yes"
            ]

        return bool(value)


    def settings_int(self, key, default=0):
        value = self.ui_settings.value(key, default)

        try:
            return int(value)
        except Exception:
            return default


    def restore_combo_value(self, combo, key, default):
        value = self.ui_settings.value(key, default)
        index = combo.findText(value)
        if index < 0:
            return
        combo.setCurrentIndex(index)


    def restore_ui_state(self):
        geometry = self.ui_settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        splitter_state = self.ui_settings.value("window/main_splitter")

        if splitter_state:
            self.main_splitter.restoreState(splitter_state)
        self.tool_panel.native_rotation_axes_checkbox.setChecked(self.settings_bool("tool/maya_lra", False))

        self.restore_combo_value(self.tool_panel.primary_combo,"tool/primary_axis","X")
        self.restore_combo_value(self.tool_panel.secondary_combo,"tool/secondary_axis","Y")
        self.restore_combo_value(self.tool_panel.mode_combo,"tool/secondary_mode","World")

        self.settings_panel.show_overlay_checkbox.setChecked(self.settings_bool("settings/show_overlay", True))
        self.settings_panel.show_delta_heatmap_checkbox.setChecked(self.settings_bool("settings/show_delta_heatmap", False))
        self.settings_panel.live_sync_checkbox.setChecked(self.settings_bool("settings/live_sync", True))
        self.settings_panel.show_plane_checkbox.setChecked(self.settings_bool("settings/show_plane", True))
        self.settings_panel.flip_plane_checkbox.setChecked(self.settings_bool("settings/flip_plane", False))
        self.settings_panel.average_normals_checkbox.setChecked(self.settings_bool("settings/average_normals", True))
        self.settings_panel.show_grid_checkbox.setChecked(self.settings_bool("settings/show_grid", True))
        self.settings_panel.orient_end_joint_checkbox.setChecked(self.settings_bool("settings/orient_end_joint", True))
        self.settings_panel.show_joint_names_checkbox.setChecked(self.settings_bool("settings/show_joint_names", False))
        self.settings_panel.split_branches_checkbox.setChecked(self.settings_bool("settings/split_branches", False))
        self.settings_panel.show_axis_gizmo_checkbox.setChecked(self.settings_bool("settings/show_axis_gizmo", True))
        self.settings_panel.show_3d_joints_checkbox.setChecked(self.settings_bool("settings/show_3d_joints", True))
        self.settings_panel.show_current_axes_checkbox.setChecked(self.settings_bool("settings/show_current_axes", True))
        self.settings_panel.show_preview_axes_checkbox.setChecked(self.settings_bool("settings/show_preview_axes", True))

        self.restore_combo_value(self.settings_panel.projection_combo,"settings/projection","Orbit")
        self.settings_panel.axis_length_spinbox.setValue(self.settings_int("settings/axis_length",28))
        self.settings_panel.joint_size_spinbox.setValue(self.settings_int("settings/joint_size",5))
        self.settings_panel.normal_length_spinbox.setValue(self.settings_int("settings/normal_length",60))

        self.cache_panel.lock_selection_checkbox.setChecked(self.settings_bool("cache/lock_cache", True))
        self.cache_panel.apply_cached_chain_checkbox.setChecked(self.settings_bool("cache/apply_cached", True))


    def save_ui_state(self):
        self.ui_settings.setValue("window/geometry",self.saveGeometry())
        self.ui_settings.setValue("window/main_splitter",self.main_splitter.saveState())
        self.ui_settings.setValue("tool/maya_lra",self.tool_panel.native_rotation_axes_enabled())
        self.ui_settings.setValue("tool/primary_axis",self.tool_panel.primary_axis())
        self.ui_settings.setValue("tool/secondary_axis",self.tool_panel.secondary_axis())
        self.ui_settings.setValue("tool/secondary_mode",self.tool_panel.secondary_mode())
        self.ui_settings.setValue("settings/show_overlay",self.settings_panel.show_overlay())
        self.ui_settings.setValue("settings/show_delta_heatmap",self.settings_panel.show_delta_heatmap())
        self.ui_settings.setValue("settings/live_sync",self.settings_panel.live_sync_enabled())
        self.ui_settings.setValue("settings/show_plane",self.settings_panel.show_plane())
        self.ui_settings.setValue("settings/flip_plane",self.settings_panel.flip_plane())
        self.ui_settings.setValue("settings/average_normals",self.settings_panel.average_normals())
        self.ui_settings.setValue("settings/show_grid",self.settings_panel.show_grid())
        self.ui_settings.setValue("settings/orient_end_joint",self.settings_panel.orient_end_joint())
        self.ui_settings.setValue("settings/show_joint_names",self.settings_panel.show_joint_names())
        self.ui_settings.setValue("settings/split_branches",self.settings_panel.split_branches())
        self.ui_settings.setValue("settings/show_axis_gizmo",self.settings_panel.show_axis_gizmo())
        self.ui_settings.setValue("settings/show_3d_joints",self.settings_panel.show_3d_joints())
        self.ui_settings.setValue("settings/show_current_axes",self.settings_panel.show_current_axes())
        self.ui_settings.setValue("settings/show_preview_axes",self.settings_panel.show_preview_axes())
        self.ui_settings.setValue("settings/projection",self.settings_panel.projection_mode())
        self.ui_settings.setValue("settings/axis_length",self.settings_panel.axis_length())
        self.ui_settings.setValue("settings/joint_size",self.settings_panel.joint_size())
        self.ui_settings.setValue("settings/normal_length",self.settings_panel.normal_length())
        self.ui_settings.setValue("cache/lock_cache",self.cache_panel.is_cache_locked())
        self.ui_settings.setValue("cache/apply_cached",self.cache_panel.apply_cached())

        self.ui_settings.sync()

    def build_ui(self):
        margins = 4

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(
            margins,
            margins,
            margins,
            margins
        )

        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self.controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QVBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(
            margins,
            margins,
            margins,
            margins
        )
        controls_layout.setSpacing(4)

        self.viewport_widget = QtWidgets.QWidget()
        viewport_layout = QtWidgets.QVBoxLayout(self.viewport_widget)
        viewport_layout.setContentsMargins(
            margins,
            margins,
            margins,
            margins
        )
        viewport_layout.setSpacing(4)

        self.viewport_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        self.tool_panel = JOWToolPanel()
        self.cache_panel = JOWCachePanel()
        self.settings_panel = JOWSettingsPanel()

        controls_layout.addWidget(self.tool_panel)
        controls_layout.addWidget(self.cache_panel)
        controls_layout.addWidget(self.settings_panel)

        self.viewport = JOW_viewport.JOWViewport()
        self.viewport.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        viewport_layout.addWidget(
            self.viewport,
            1
        )

        bottom_actions_layout = QtWidgets.QHBoxLayout()
        bottom_actions_layout.setContentsMargins(0, 0, 0, 0)
        bottom_actions_layout.setSpacing(4)

        self.apply_btn = create_action_button(
            "Apply Orientation",
            minimum_width=150
        )

        bottom_actions_layout.addStretch(1)

        bottom_actions_layout.addWidget(self.apply_btn)

        viewport_layout.addLayout(bottom_actions_layout)

        self.warning_label = QtWidgets.QLabel("Logger: ")
        self.warning_label.setStyleSheet("color: #ffcc66;")
        self.warning_label.setWordWrap(True)

        viewport_layout.addWidget(self.warning_label)

        self.main_splitter.addWidget(self.controls_widget)

        self.main_splitter.addWidget(self.viewport_widget)

        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([245, 520])

        main_layout.addWidget(
            self.main_splitter
        )

    ##########################################################
    # Signals
    ##########################################################

    def connect_signals(self):
        self.tool_panel.settings_changed.connect(self.refresh_preview_from_ui)
        self.tool_panel.create_guide_requested.connect(self.create_guide)
        self.tool_panel.select_guide_requested.connect(self.select_guide)
        self.tool_panel.delete_guide_requested.connect(self.delete_guide)
        self.tool_panel.pick_custom_object_requested.connect(self.pick_custom_object)

        self.cache_panel.replace_cache_requested.connect(self.refresh_cache_from_selection)
        self.cache_panel.add_selection_requested.connect(self.add_selection_to_cache)
        self.cache_panel.remove_selected_requested.connect(self.remove_selected_cached_roots)
        self.cache_panel.clear_cache_requested.connect(self.clear_cached_chain)
        self.cache_panel.cached_root_double_clicked.connect(self.select_cached_root)
        self.cache_panel.lock_cache_toggled.connect(self.on_lock_selection_changed)
        self.cache_panel.apply_cached_toggled.connect(self.refresh_preview_from_ui)

        self.settings_panel.display_options_changed.connect(self.update_viewport_display_options)
        self.settings_panel.preview_settings_changed.connect(self.refresh_preview_from_ui)
        self.settings_panel.sizes_changed.connect(self.update_viewport_sizes)
        self.settings_panel.live_sync_toggled.connect(self.update_live_sync_state)

        self.tool_panel.native_rotation_axes_toggled.connect(self.set_cached_native_rotation_axes_visibility)

        self.settings_panel.projection_changed.connect(self.change_projection)
        self.settings_panel.frame_preview_requested.connect(self.frame_preview)
        self.settings_panel.frame_selected_requested.connect(self.frame_selected_joint)
        self.settings_panel.reset_view_requested.connect(self.reset_view)

        self.viewport.joint_clicked.connect(self.select_joint_from_viewport)
        self.viewport.guide_clicked.connect(self.select_guide_from_viewport)
        self.viewport.viewport_empty_clicked.connect(self.clear_selection_from_viewport)

        self.apply_btn.clicked.connect(self.apply_orientation)

    ##########################################################
    # Settings
    ##########################################################

    def get_settings(self):
        settings = OrientationSettings(
            primary_axis=self.tool_panel.primary_axis(),
            secondary_axis=self.tool_panel.secondary_axis(),
            secondary_mode=self.tool_panel.secondary_mode(),
            flip_plane=self.settings_panel.flip_plane(),
            average_normals=self.settings_panel.average_normals(),
            orient_end_joint=self.settings_panel.orient_end_joint()
        )
        settings.split_branches = self.settings_panel.split_branches()
        if self.cache_panel.apply_cached():
            settings.roots = JOW_preview.get_preview_roots()
            roots_for_mapping = settings.roots
        else:
            roots_for_mapping = JOW_maya_joints.get_unique_roots_from_selection()

        if settings.secondary_mode == "Custom Object":
            settings.custom_object = JOW_preview.get_cached_custom_object()

            if settings.custom_object:
                short_custom_object = JOW_maya_nodes.short_name(settings.custom_object)
                is_jow_guide = short_custom_object.startswith("JOW_Guide_LOC_")
                is_shared_guide = (short_custom_object == "JOW_Guide_LOC_SHARED")

                if is_jow_guide and not is_shared_guide:
                    settings.custom_object = None

            orient_roots_for_mapping = JOW_preview.get_orient_roots_for_roots(
                roots_for_mapping,
                settings
            )
            settings.custom_objects_by_root = (
                JOW_preview.get_custom_objects_by_root_for_roots(
                    orient_roots_for_mapping,
                    fallback_custom_object=settings.custom_object
                )
            )

        return settings

    ##########################################################
    # Script Jobs
    ##########################################################

    def create_selection_script_job(self):
        self.delete_selection_script_job()

        self.selection_script_job = cmds.scriptJob(
            event=[
                "SelectionChanged",
                self.on_maya_selection_changed
            ],
            protected=True
        )

    def delete_selection_script_job(self):
        if not self.selection_script_job:
            return

        if cmds.scriptJob(exists=self.selection_script_job):
            cmds.scriptJob(
                kill=self.selection_script_job,
                force=True
            )

        self.selection_script_job = None

    def on_maya_selection_changed(self):
        if self._syncing_selection_from_viewport:
            self.update_set_cache_button_state()
            return

        self.sync_viewport_selection_from_maya()
        self.update_set_cache_button_state()

    def cleanup_before_delete(self):
        try:
            self.stop_live_sync_timer()
        except Exception:
            pass

        try:
            self.delete_selection_script_job()
        except Exception:
            pass

        try:
            self.set_cached_native_rotation_axes_visibility(False)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            self.save_ui_state()
        except Exception:
            pass

        self.cleanup_before_delete()

        QtWidgets.QDialog.closeEvent(
            self,
            event
        )

    ##########################################################
    # Cache
    ##########################################################

    def refresh_cache_panel(self):
        removed_count = JOW_preview.validate_cache_and_get_removed_count()
        roots = JOW_preview.get_cached_roots()
        custom_object = JOW_preview.get_cached_custom_object()
        guide_summary_text = JOW_preview.get_cached_guide_summary_text()

        self.cache_panel.update_cache_display(
            roots,
            custom_object,
            guide_summary_text=guide_summary_text
        )

        if removed_count > 0:
            self.set_warning(
                "{} cached root(s) no longer exist and were removed.".format(
                    removed_count
                )
            )

        self.update_set_cache_button_state()

    def refresh_cache_from_selection(self):
        roots = JOW_preview.refresh_cache_from_selection()

        self.refresh_cache_panel()
        self.refresh_preview()
        self.reset_live_sync_snapshot()
        self.update_set_cache_button_state()

        if roots:
            self.set_warning(
                "Cache replaced from selection: {} root(s).".format(
                    len(roots)
                )
            )
        else:
            self.set_warning("No joint roots found in selection.")

    def clear_cached_chain(self):
        JOW_preview.clear_cache()

        self.viewport.set_preview_chains([])
        self.viewport.set_selected_joints([])
        self.viewport.set_selected_guides([])

        self.live_sync_snapshot = {}

        self.refresh_cache_panel()
        self.set_warning("Cache cleared.")
        self.update_set_cache_button_state()

    def add_selection_to_cache(self):
        roots = JOW_preview.get_unique_roots_from_selection_for_cache()

        if not roots:
            self.set_warning(
                "Select one or more joints to add their root chains to the cache."
            )
            return

        JOW_preview.add_roots_to_cache(
            roots
        )

        self.refresh_cache_panel()
        self.refresh_preview()
        self.reset_live_sync_snapshot()
        self.update_set_cache_button_state()

        self.set_warning(
            "Added {} root(s) to cache.".format(
                len(roots)
            )
        )

    def remove_selected_cached_roots(self, roots):
        if not roots:
            self.set_warning("Select one or more cached roots to remove.")
            return

        JOW_preview.remove_cached_roots(roots)
        self.refresh_cache_panel()
        self.refresh_preview(preserve_cache=True)

        self.reset_live_sync_snapshot()
        self.update_set_cache_button_state()

        self.set_warning(
            "Removed {} cached root(s).".format(
                len(roots)
            )
        )

    def select_cached_root(self, root):
        if not root:
            return

        if not cmds.objExists(root):
            self.set_warning(
                "Cached root no longer exists: {}".format(root)
            )

            self.refresh_cache_panel()
            return

        cmds.select(root,r=True)
        self.viewport.set_selected_joints([root])
        self.viewport.set_selected_guides([])

        self.sync_viewport_selection_from_maya()
        self.update_set_cache_button_state()

        self.set_warning(
            "Selected cached root: {}".format(
                root.split("|")[-1]
            )
        )

    def selection_has_joint(self):
        selected = cmds.ls(
            sl=True,
            long=True
        ) or []

        if not selected:
            return False

        joints = cmds.ls(
            selected,
            type="joint",
            long=True
        ) or []

        return bool(joints)

    def cache_is_empty(self):
        roots = JOW_preview.get_cached_roots()

        return not bool(roots)

    def update_set_cache_button_state(self):
        should_prompt_cache = (
            self.cache_is_empty() and
            self.selection_has_joint()
        )

        self.cache_panel.update_set_cache_prompt(should_prompt_cache)

    def on_lock_selection_changed(self, *args):
        JOW_preview.set_cache_locked(
            self.cache_panel.is_cache_locked()
        )

        self.refresh_cache_panel()
        self.refresh_preview()

    def get_cached_joint_nodes(self):
        nodes = []

        roots = JOW_preview.get_cached_roots()

        for root in roots:
            if not cmds.objExists(root):
                continue

            joints = JOW_maya_joints.get_chain_joints(root)

            for joint in joints:
                if not cmds.objExists(joint):
                    continue

                if joint not in nodes:
                    nodes.append(
                        joint
                    )

        return nodes
    ##########################################################
    # Viewport Display
    ##########################################################

    def update_viewport_display_options(self, *args):
        self.viewport.set_show_grid(self.settings_panel.show_grid())
        self.viewport.set_show_axis_gizmo(self.settings_panel.show_axis_gizmo())
        self.viewport.set_show_3d_joints(self.settings_panel.show_3d_joints())
        self.viewport.set_show_curve_plane_surface(self.settings_panel.show_plane())
        self.viewport.set_show_current_axes(self.settings_panel.show_current_axes())
        self.viewport.set_show_preview_axes(self.settings_panel.show_preview_axes())
        self.viewport.set_show_overlay(self.settings_panel.show_overlay())
        self.viewport.set_show_delta_heatmap(self.settings_panel.show_delta_heatmap())

        self.viewport.update()

    def update_viewport_sizes(self):
        self.viewport.set_axis_length(self.settings_panel.axis_length())
        self.viewport.set_joint_size(self.settings_panel.joint_size())
        self.viewport.set_normal_length(self.settings_panel.normal_length())

        self.viewport.update()

    def frame_preview(self):
        self.viewport.frame_preview()

    def frame_selected_joint(self):
        self.viewport.frame_selected_joint()

    ##########################################################
    # Logger
    ##########################################################

    def set_warning(self, message):
        self.warning_label.setText(message)

    def clear_warning(self):
        self.warning_label.setText("")

    ##########################################################
    # Guide Manager
    ##########################################################

    def create_guide(self):
        selected_roots = self.get_selected_roots_for_guide_action()
        if selected_roots:
            position = self.get_average_center_for_roots(selected_roots)

            # Use the first selected orient root only for naming.
            # The guide itself will be assigned to all selected roots.
            guide = JOW_guides.create_guide_for_root(
                selected_roots[0],
                position=position
            )

            if not guide:
                self.set_warning("No guide was created.")
                return

            for root in selected_roots:
                JOW_preview.set_cached_guide_for_root(root, guide)

            JOW_maya_selection.select_node(guide, replace=True)

            self.viewport.set_selected_guide(guide)
            self.viewport.set_selected_joints([])

            self.set_warning("Created one guide for {} selected chain(s).".format(len(selected_roots)))

        else:
            cached_roots = self.get_cached_roots_for_guide_action()
            settings = self.get_settings()

            orient_roots = JOW_preview.get_orient_roots_for_roots(cached_roots, settings)
            target_roots = JOW_preview.get_roots_without_per_root_guides(orient_roots)

            if not cached_roots:
                self.set_warning("Select a joint or cache one or more chains before creating a guide.")
                return

            if not target_roots:
                self.set_warning("All cached roots already have per-chain guides.")
                return

            position = self.get_average_center_for_roots(target_roots)
            guide = JOW_guides.create_shared_guide(position=position)

            JOW_preview.set_cached_custom_object(guide)
            JOW_maya_selection.select_node(guide, replace=True)

            self.viewport.set_selected_joints([])
            self.viewport.set_selected_guide(guide)

            self.set_warning(
                "Created shared guide for {} unguided cached root(s).".format(
                    len(target_roots)
                )
            )

        self.refresh_cache_panel()
        self.refresh_preview(preserve_cache=True)
        self.reset_live_sync_snapshot()

    def select_guide(self):
        selected_roots = self.get_selected_roots_for_guide_action()
        guides = []

        if selected_roots:
            for root in selected_roots:
                guide = JOW_preview.get_cached_guide_for_root(root)
                if not guide:
                    continue
                if guide in guides:
                    continue

                guides.append(guide)
        else:
            guides = JOW_guides.get_all_guides()

        selected_guides = JOW_guides.select_guides(guides)

        if not selected_guides:
            self.set_warning("No cached guide found for the current selection.")
            return

        self.viewport.set_selected_joints([])
        self.viewport.set_selected_guides(selected_guides)

        self.refresh_cache_panel()
        self.refresh_preview(preserve_cache=True)

        self.set_warning("Selected {} guide(s).".format(len(selected_guides)))

    def validate_viewport_selected_guide(self):
        selected_guide = self.viewport.selected_guide

        if not selected_guide:
            return
        if cmds.objExists(selected_guide):
            return

        self.viewport.set_selected_guide(None)

    def delete_guide(self):
        guides_to_delete = JOW_guides.get_selected_guides()

        if not guides_to_delete:
            guides_to_delete = JOW_guides.get_all_guides()
        if not guides_to_delete:
            self.set_warning("No JOW guide locator exists.")
            return

        JOW_preview.clear_cached_guides_for_guides(guides_to_delete)
        deleted_guides = JOW_guides.delete_guides(guides_to_delete)
        self.clear_deleted_guides_from_viewport(deleted_guides)

        self.refresh_cache_panel()
        self.refresh_preview(preserve_cache=True)
        self.reset_live_sync_snapshot()

        self.set_warning("Deleted {} guide(s).".format(len(deleted_guides)))

        self.viewport.update()

    def pick_custom_object(self):
        custom_object = JOW_guides.get_selected_custom_object()

        if not custom_object:
            self.set_warning(
                "Select a non-joint object to use as Custom Object guide."
            )
            return

        selected_roots = self.get_selected_roots_for_guide_action()

        if selected_roots:
            for root in selected_roots:
                JOW_preview.set_cached_guide_for_root(root,custom_object)

            self.set_warning(
                "Custom Object assigned to {} selected chain(s): {}".format(
                    len(selected_roots),
                    custom_object.split("|")[-1]
                )
            )

        else:
            JOW_preview.set_cached_custom_object(custom_object)

            self.set_warning(
                "Custom Object picked as shared guide: {}".format(
                    custom_object.split("|")[-1]
                )
            )

        self.refresh_cache_panel()
        self.refresh_preview(preserve_cache=True)
        self.reset_live_sync_snapshot()

    def get_selected_roots_for_guide_action(self):
        settings = self.get_settings()

        return JOW_maya_joints.get_unique_orient_roots_from_selection(
            split_branches=getattr(
                settings,
                "split_branches",
                False
            )
        )

    def get_cached_roots_for_guide_action(self):
        return JOW_preview.get_cached_roots()

    def get_chain_center_for_root(self, root):
        settings = self.get_settings()

        if getattr(settings, "split_branches", False):
            joint_chains = JOW_maya_joints.get_linear_chains_from_root(root)
            if joint_chains:
                return JOW_preview.get_chain_center(joint_chains[0])
        joints = JOW_maya_joints.get_chain_joints(root)

        return JOW_preview.get_chain_center(joints)

    def get_average_center_for_roots(self, roots):
        centers = []

        for root in roots or []:
            center = self.get_chain_center_for_root(root)

            if center is None:
                continue

            centers.append(center)

        if not centers:
            return None

        result = JOW_maya_transforms.vector_from_position([0, 0, 0])

        for center in centers:
            result += center

        result /= len(centers)

        return result

    def clear_deleted_guides_from_viewport(self, deleted_guides):
        selected_guides = getattr(
            self.viewport,
            "selected_guides",
            []
        )

        remaining_guides = []
        for selected_guide in selected_guides:
            should_remove = False
            for deleted_guide in deleted_guides or []:
                if JOW_preview.nodes_match(
                    selected_guide,
                    deleted_guide
                ):
                    should_remove = True
                    break

            if should_remove:
                continue

            remaining_guides.append(selected_guide)
        self.viewport.set_selected_guides(remaining_guides)

    ##########################################################
    # Preview / Apply
    ##########################################################

    def change_projection(self, projection_mode):
        self.viewport.set_projection_mode(projection_mode)
        self.focus_viewport()

    def reset_view(self):
        self.viewport.reset_view()

    def refresh_preview_from_ui(self, *args):
        self.refresh_preview(preserve_cache=False)

    def refresh_preview(self, preserve_cache=False):
        old_cache_locked_state = JOW_preview.is_cache_locked()

        if preserve_cache:
            JOW_preview.set_cache_locked(True)
        else:
            JOW_preview.set_cache_locked(self.cache_panel.is_cache_locked())

        try:
            self.validate_viewport_selected_guide()
            settings = self.get_settings()

            if self.cache_panel.apply_cached():
                apply_target_label = "Cached Chain"
            else:
                apply_target_label = "Selection"

            self.viewport.set_overlay_context(settings, apply_target_label)

            preview_chains = JOW_preview.build_preview_chains(settings)

            custom_object_missing = (
                settings.secondary_mode == "Custom Object" and
                not JOW_preview.preview_chains_have_guides(preview_chains)
            )

            if custom_object_missing:
                self.set_warning("Custom Object mode needs a valid non-joint guide object.")

            self.viewport.set_secondary_mode(settings.secondary_mode)
            self.viewport.set_show_joint_names(self.settings_panel.show_joint_names())
            self.viewport.set_preview_chains(preview_chains)

            self.sync_viewport_selection_from_maya()
            self.refresh_cache_panel()

            if not preview_chains:
                self.set_warning("No valid cached or selected joint chains found.")

            elif custom_object_missing:
                self.set_warning("Custom Object mode needs a valid non-joint guide object.")

            else:
                self.clear_warning()

            self.focus_viewport()

        finally:
            if preserve_cache:
                JOW_preview.set_cache_locked(
                    old_cache_locked_state
                )

    def apply_orientation(self):
        settings = self.get_settings()

        if (
            self.cache_panel.apply_cached() and
            not settings.roots
        ):
            self.set_warning("Apply To Cached Chain is enabled, but no cached chain exists."            )
            return
        JOW_core.apply_orientation(settings)

        self.refresh_preview()
        self.reset_live_sync_snapshot()

    def focus_viewport(self):
        self.viewport.setFocus()

    ##########################################################
    # Viewport Selection
    ##########################################################

    def select_joint_from_viewport(self, joint_name):
        if not joint_name:
            return

        if not cmds.objExists(joint_name):
            return

        self._syncing_selection_from_viewport = True

        try:
            cmds.select(joint_name, r=True)

            self.viewport.set_selected_guides([])
            self.viewport.set_selected_joints([joint_name])

        finally:
            self._syncing_selection_from_viewport = False

        self.update_set_cache_button_state()

    def select_guide_from_viewport(self, guide_name):
        if not guide_name:
            return
        if not JOW_maya_nodes.exists(guide_name):
            return

        self._syncing_selection_from_viewport = True
        try:
            JOW_maya_selection.select_node(guide_name, replace=True)

            self.viewport.set_selected_joints([])
            self.viewport.set_selected_guides([guide_name])

        finally:
            self._syncing_selection_from_viewport = False

        self.refresh_cache_panel()
        self.update_set_cache_button_state()

        self.set_warning("Guide selected from viewport: {}".format(guide_name.split("|")[-1]))

    def clear_selection_from_viewport(self):
        self._syncing_selection_from_viewport = True

        try:
            cmds.select(
                clear=True
            )

            self.viewport.set_selected_joints([])
            self.viewport.set_selected_guides([])

        finally:
            self._syncing_selection_from_viewport = False

        self.update_set_cache_button_state()

    ##########################################################
    # Native Maya Selection Sync
    ##########################################################

    def get_selected_maya_items(self):
        return JOW_maya_selection.get_selection(long=True)

    def get_first_selected_maya_item(self):
        selected = cmds.ls(
            sl=True,
            long=True
        ) or []

        if not selected:
            return None

        return selected[0]

    def maya_item_is_preview_guide(self, item):
        if not item:
            return False

        if not cmds.objExists(item):
            return False

        for chain in self.viewport.preview_chains:
            if not chain.guide:
                continue

            if not chain.guide.name:
                continue

            if JOW_preview.nodes_match(chain.guide.name, item):
                return True

        return False

    def maya_item_is_preview_joint(self, item):
        if not item:
            return False

        if not cmds.objExists(item):
            return False

        for chain in self.viewport.preview_chains:
            for joint in chain.joints:
                if joint.name == item:
                    return True

        return False

    def sync_viewport_selection_from_maya(self):
        selected_items = JOW_maya_selection.get_selection() or []

        if not selected_items:
            self.viewport.set_selected_joints([])
            self.viewport.set_selected_guides([])
            return

        selected_guides = []

        for item in selected_items:
            for chain in self.viewport.preview_chains:
                if not chain.guide:
                    continue

                if not chain.guide.name:
                    continue

                if not JOW_preview.nodes_match(chain.guide.name, item):
                    continue

                if chain.guide.name not in selected_guides:
                    selected_guides.append(chain.guide.name)

                break

        if selected_guides:
            self.viewport.set_selected_joints([])
            self.viewport.set_selected_guides(selected_guides)
            return

        selected_joints = []

        for item in selected_items:
            for chain in self.viewport.preview_chains:
                for joint in chain.joints:
                    if joint.name != item:
                        continue
                    if joint.name not in selected_joints:
                        selected_joints.append(joint.name)

                    break

        if selected_joints:
            self.viewport.set_selected_guides([])
            self.viewport.set_selected_joints(selected_joints)
            return

        self.viewport.set_selected_joints([])
        self.viewport.set_selected_guides([])

    ##########################################################
    # Native Maya Viewport Live Sync
    ##########################################################

    def create_live_sync_timer(self):
        self.live_sync_timer = QtCore.QTimer(self)

        self.live_sync_timer.setInterval(
            self.live_sync_interval_ms
        )

        self.live_sync_timer.timeout.connect(
            self.check_live_sync_matrix_changes
        )

        self.reset_live_sync_snapshot()

        if self.settings_panel.live_sync_enabled():
            self.live_sync_timer.start()

    def update_live_sync_state(self, *args):
        if not self.live_sync_timer:
            return

        if self.settings_panel.live_sync_enabled():
            self.reset_live_sync_snapshot()
            self.live_sync_timer.start()

        else:
            self.live_sync_timer.stop()
            self.live_sync_snapshot = {}

    def stop_live_sync_timer(self):
        if not self.live_sync_timer:
            return

        self.live_sync_timer.stop()

    def get_live_sync_nodes(self):
        nodes = []

        roots = JOW_preview.get_cached_roots()

        cached_joints = JOW_maya_joints.get_unique_joint_chains_from_roots(roots)

        for joint in cached_joints:
            if joint in nodes:
                continue

            nodes.append(joint)

        guides_by_root = JOW_preview.get_cached_guides_by_root()

        for guide in guides_by_root.values():
            if not JOW_maya_nodes.exists(guide):
                continue

            if guide in nodes:
                continue

            nodes.append(guide)

        custom_object = JOW_preview.get_cached_custom_object()

        if custom_object and JOW_maya_nodes.exists(custom_object):
            if custom_object not in nodes:
                nodes.append(custom_object)

        return nodes

    def reset_live_sync_snapshot(self):#easeOfReadWrapperReally
        self.live_sync_snapshot = JOW_maya_transforms.get_world_matrix_snapshot(self.get_live_sync_nodes())


    def snapshots_are_different(self, snapshot_a, snapshot_b):
        return JOW_maya_transforms.snapshots_are_different(
            snapshot_a,
            snapshot_b,
            tolerance=self.live_sync_tolerance
        )

    def check_live_sync_matrix_changes(self):
        if self._live_sync_refreshing:
            return

        if not self.settings_panel.live_sync_enabled():
            return

        new_snapshot = JOW_maya_transforms.get_world_matrix_snapshot(
            self.get_live_sync_nodes()
        )

        if not JOW_maya_transforms.snapshots_are_different(
            self.live_sync_snapshot,
            new_snapshot,
            self.live_sync_tolerance
        ):
            return

        self.live_sync_snapshot = new_snapshot
        self.refresh_preview_from_live_sync()

    def refresh_preview_from_live_sync(self):
        if self._live_sync_refreshing:
            return

        self._live_sync_refreshing = True

        try:
            self.refresh_preview(
                preserve_cache=True
            )

            self.reset_live_sync_snapshot()

        finally:
            self._live_sync_refreshing = False

    @undo_chunk
    def set_cached_native_rotation_axes_visibility(self, state):
        cached_joints = set(self.get_cached_joint_nodes())

        nodes_to_disable = (
            self.native_rotation_axis_nodes - cached_joints
        )

        for node in nodes_to_disable:
            self.set_node_native_rotation_axis_visibility(
                node,
                False
            )

        for joint in cached_joints:
            self.set_node_native_rotation_axis_visibility(
                joint,
                state
            )

        if state:
            self.native_rotation_axis_nodes = cached_joints
        else:
            self.native_rotation_axis_nodes = set()

        cmds.refresh()

    def set_node_native_rotation_axis_visibility(
        self,
        node,
        state
    ):
        if not node:
            return

        if not cmds.objExists(node):
            return

        attribute = "{}.displayLocalAxis".format(
            node
        )

        if not cmds.objExists(attribute):
            return

        try:
            cmds.setAttr(
                attribute,
                bool(state)
            )

        except Exception:
            pass