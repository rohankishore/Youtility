import json
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QComboBox, QFileDialog, QColorDialog
from qfluentwidgets import (LineEdit, TextEdit,
                            ScrollArea, StrongBodyLabel, MessageBox)

with open("resources/misc/config.json", "r") as themes_file:
    _themes = json.load(themes_file)


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Settings")
        self.initUI()

    def initUI(self):
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

        self.def_sub_format = QComboBox()
        self.def_sub_format.addItems(["SRT", "XML"])
        self.def_sub_format.setCurrentText(_themes["def_sub_format"])
        pref_layout.addWidget(self.def_sub_format)

        # Apply Button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.save_json)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)


    def save_json(self):
        _themes["theme"] = self.theme_color_line_edit.text()
        _themes["def_sub_format"] = self.def_sub_format.currentText()

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
