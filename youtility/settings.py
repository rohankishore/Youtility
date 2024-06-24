import json

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QComboBox, QSpacerItem
from qfluentwidgets import (LineEdit, StrongBodyLabel, MessageBox, CheckBox, ComboBox)

with open("resources/misc/config.json", "r") as themes_file:
    _themes = json.load(themes_file)


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Settings")
        self.initUI()

    def initUI(self):

        spacer_item_small = QSpacerItem(0, 10)
        spacer_item_medium = QSpacerItem(0, 20)

        layout = QVBoxLayout()
        layout.addStretch()

        theming_group = QGroupBox("Theming")
        theming_layout = QVBoxLayout(theming_group)
        layout.addWidget(theming_group)

        pref_group = QGroupBox("Preferences")
        pref_layout = QVBoxLayout(pref_group)
        layout.addWidget(pref_group)

        # Theme Color Label
        theme_color_label = StrongBodyLabel("Theme Color: ", self)
        theming_layout.addWidget(theme_color_label)

        # Theme Color Line Edit
        self.theme_color_line_edit = LineEdit()
        self.theme_color_line_edit.setText(_themes["theme"])
        theming_layout.addWidget(self.theme_color_line_edit)

        def_sub_format_label = StrongBodyLabel("Default Subtitle Format: ", self)
        pref_layout.addWidget(def_sub_format_label)
        self.def_sub_format = ComboBox()
        self.def_sub_format.addItems(["SRT", "XML"])
        self.def_sub_format.setCurrentText(_themes["def_sub_format"])
        pref_layout.addWidget(self.def_sub_format)

        pref_layout.addSpacerItem(spacer_item_medium)

        self.set_progressive = CheckBox()
        self.set_progressive.setText("Allow higher res downloads (audio may be missing): ")
        if _themes["progressive"] == "False":
            self.set_progressive.setChecked(True)
        else:
            pass
        pref_layout.addWidget(self.set_progressive)

        # Apply Button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.save_json)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def save_json(self):
        progressive_state = "True"
        if self.set_progressive.isChecked():
            progressive_state = "False"
        else:
            progressive_state = "True"

        _themes["theme"] = self.theme_color_line_edit.text()
        _themes["def_sub_format"] = self.def_sub_format.currentText()
        _themes["progressive"] = progressive_state

        with open("resources/misc/config.json", "w") as json_file:
            json.dump(_themes, json_file)

        w = MessageBox(
            'Settings Applied!',
            "Restart Youtility to view the changes",
            self
        )
        w.yesButton.setText('Cool 🤝')
        w.cancelButton.setText('Extra Cool 😘')

        if w.exec():
            pass
