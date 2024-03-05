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

        # Theme Color Label
        theme_color_label = StrongBodyLabel()
        theme_color_label.setText("Theme Color:")
        layout.addWidget(theme_color_label)

        # Theme Color Line Edit
        self.theme_color_line_edit = LineEdit()
        self.theme_color_line_edit.setText(_themes["theme"])
        layout.addWidget(self.theme_color_line_edit)

        # Theme Color Button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.save_json)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)


    def save_json(self):
        _themes["theme"] = self.theme_color_line_edit.text()

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
