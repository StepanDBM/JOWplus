try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide6 import QtWidgets


TOGGLE_BUTTON_STYLE = """
QPushButton {
    background-color: #4a4a4a;
    color: #dddddd;
    border: 1px solid #666666;
    border-radius: 3px;
    padding: 3px 8px;
}

QPushButton:hover {
    background-color: #575757;
    border: 1px solid #777777;
}

QPushButton:checked {
    background-color: #2f6f9f;
    color: #ffffff;
    border: 1px solid #70b8e8;
    font-weight: bold;
}

QPushButton:checked:hover {
    background-color: #367fb8;
    border: 1px solid #8fd0ff;
}

QPushButton:disabled {
    background-color: #333333;
    color: #777777;
    border: 1px solid #444444;
}
"""


ACTION_BUTTON_STYLE = """
QPushButton {
    background-color: #505050;
    color: #eeeeee;
    border: 1px solid #666666;
    border-radius: 3px;
    padding: 3px 8px;
}

QPushButton:hover {
    background-color: #5f5f5f;
    border: 1px solid #777777;
}

QPushButton:pressed {
    background-color: #3f3f3f;
}

QPushButton:disabled {
    background-color: #333333;
    color: #777777;
    border: 1px solid #444444;
}
"""


CACHE_PROMPT_BUTTON_STYLE = """
QPushButton {
    background-color: #2fa84f;
    color: #ffffff;
    font-weight: bold;
    border: 1px solid #7dff9d;
    border-radius: 3px;
    padding: 3px 8px;
}

QPushButton:hover {
    background-color: #36c45d;
}

QPushButton:pressed {
    background-color: #23883f;
}
"""


def create_toggle_button(
    text,
    checked=False,
    tooltip=None,
    minimum_width=88
):
    button = QtWidgets.QPushButton(text)
    button.setCheckable(True)
    button.setChecked(checked)
    button.setMinimumWidth(minimum_width)
    button.setMinimumHeight(24)
    button.setStyleSheet(TOGGLE_BUTTON_STYLE)

    if tooltip:
        button.setToolTip(tooltip)

    return button


def create_action_button(
    text,
    tooltip=None,
    minimum_width=88
):
    button = QtWidgets.QPushButton(text)
    button.setMinimumWidth(minimum_width)
    button.setMinimumHeight(24)
    button.setStyleSheet(ACTION_BUTTON_STYLE)

    if tooltip:
        button.setToolTip(tooltip)

    return button


def create_toggle_grid_layout():
    layout = QtWidgets.QGridLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(4)
    layout.setVerticalSpacing(4)

    return layout