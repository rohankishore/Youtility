import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QComboBox, QFileDialog, QHBoxLayout, \
    QSpacerItem
from qfluentwidgets import (LineEdit,
                            ScrollArea, StrongBodyLabel, MessageBox, CheckBox)
from pytube import YouTube


class YoutubeVideo(QWidget):
    def __init__(self):
        super().__init__()

        spacer_item = QSpacerItem(20, 10)

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # YouTube Link Entry
        self.link_layout = QHBoxLayout()
        self.main_layout.addLayout(self.link_layout)
        self.link_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.link_entry = LineEdit(self)
        self.link_entry.setPlaceholderText("Enter YouTube Video Link: ")
        self.link_layout.addWidget(self.link_entry)

        self.main_layout.addSpacerItem(spacer_item)

        # Option menu for Quality
        self.options_layout = QHBoxLayout()
        self.main_layout.addLayout(self.options_layout)
        #quality_label = StrongBodyLabel('Quality', self)
        #self.options_layout.addWidget(quality_label)
        self.quality_menu = QComboBox()
        self.quality_menu.addItems(["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"])
        self.options_layout.addWidget(self.quality_menu)
        self.options_layout.addSpacerItem(spacer_item)
        self.thumbnail_url_checkbox = CheckBox('Copy Thumbnail Link', self)
        self.options_layout.addWidget(self.thumbnail_url_checkbox)

        self.main_layout.addSpacerItem(spacer_item)

        # Download Button
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.download_button = QPushButton("Download")
        self.button_layout.addWidget(self.download_button)

        self.setLayout(self.main_layout)


