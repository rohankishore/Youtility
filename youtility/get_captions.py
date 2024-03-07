import json
import os
import random

import pytube.exceptions
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QFileDialog, QHBoxLayout, \
    QSpacerItem, QListWidgetItem
from pytube import YouTube
from qfluentwidgets import (LineEdit,
                            StrongBodyLabel, MessageBox, ListWidget)

from consts import msgs, extension
import xml.etree.ElementTree as ET

with open("resources/misc/config.json", "r") as themes_file:
    _themes = json.load(themes_file)

def_sub_format = _themes["def_sub_format"]

class DownloaderThread(QThread):
    download_finished = pyqtSignal()

    def __init__(self, link, dwnld_list_widget,
                 main_window, save_path, ext, caption_list=None, folder_path=None):
        super().__init__()
        self.link = link
        self.caption_list = caption_list
        self.download_list_widget = dwnld_list_widget
        self.folder_path = folder_path
        self.save_path = save_path
        self.main_window = main_window
        self.ext = ext

    def run(self):
        def get_gif():
            gifs = ["loading.gif", "loading_2.gif"]
            gif = random.choice(gifs)
            gif_path = "resources/misc/" + gif
            return gif_path

        caption_file_path = ""
        if self.ext == "XML":
            caption_file_path = os.path.join(self.save_path, "captions.xml")
        else:
            caption_file_path = os.path.join(self.save_path, "captions.srt")

        # Ensure the directory exists, create it if it doesn't
        os.makedirs(self.save_path, exist_ok=True)

        youtube_client = YouTube(self.link)
        title = youtube_client.title
        youtube_client.streams.filter(file_extension=extension)

        # Download and save captions if enabled
        captions = youtube_client.captions
        language_dict = {}
        self.list_item = QListWidgetItem(
            "Downloading: " + title + " :Captions")
        self.download_list_widget.addItem(self.list_item)
        for caption in captions:
            language_name = caption.name.split(" - ")[0]  # Extracting the main language name
            language_code = caption.code.split(".")[0]  # Extracting the main language code

            if language_name not in language_dict:
                language_dict[language_name] = language_code

        lang_get = self.caption_list.currentText()
        lang = language_dict.get(lang_get)

        caption_dwnld = youtube_client.captions.get_by_language_code(lang)

        caption_dwnld_xml = caption_dwnld.xml_captions
        if self.ext == "SRT":
            caption_dwnld_xml = self.convert_xml_string_to_srt(caption_dwnld_xml)

        with open(caption_file_path, 'w', encoding="utf-8") as file:
            file.write(caption_dwnld_xml)

        self.download_finished.emit()
        self.list_item.setText((title + " :Captions" + " - Downloaded"))

    def convert_xml_string_to_srt(self, xml_string):
        root = ET.fromstring(xml_string)

        srt_content = ""
        count = 1
        for child in root.findall('.//p'):
            start = int(child.attrib.get('t', 0)) / 1000  # Convert milliseconds to seconds
            duration = int(child.attrib.get('d', 0)) / 1000  # Convert milliseconds to seconds

            if start != 0 and duration != 0:
                start_time = self.convert_time_format(start)
                end_time = self.convert_time_format(start + duration)

                srt_content += str(count) + '\n'
                srt_content += start_time + ' --> ' + end_time + '\n'
                srt_content += child.text.strip() + '\n\n'

                count += 1

        return srt_content.strip()

    def convert_time_format(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return "{:02d}:{:02d}:{:06.3f}".format(int(hours), int(minutes), seconds)


class CaptionWidget(QWidget):
    def __init__(self):
        super().__init__()

        spacer_item_small = QSpacerItem(0, 10)
        spacer_item_medium = QSpacerItem(0, 20)

        self.setObjectName("Captions")
        self.caption_list = None

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # YouTube Link Entry
        self.link_layout = QHBoxLayout()
        self.main_layout.addLayout(self.link_layout)
        self.link_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.link_entry = LineEdit(self)
        self.link_entry.textChanged.connect(self.trigger_captions_list)
        self.link_entry.setPlaceholderText("Enter YouTube Video Link: ")
        self.link_layout.addWidget(self.link_entry)

        self.main_layout.addSpacerItem(spacer_item_small)

        # Option menu for Quality
        self.quality_layout = QHBoxLayout()
        self.options_layout = QHBoxLayout()
        self.main_layout.addLayout(self.quality_layout)
        self.main_layout.addLayout(self.options_layout)
        self.ext_menu = QComboBox()
        self.ext_menu.addItems(["XML", "SRT"])
        self.ext_menu.setCurrentText(def_sub_format)
        self.quality_layout.addWidget(self.ext_menu)
        self.options_layout.addSpacerItem(spacer_item_medium)

        self.main_layout.addSpacerItem(spacer_item_small)

        self.captions_layout = QHBoxLayout()
        self.captions_layout.addSpacerItem(spacer_item_medium)
        self.main_layout.addLayout(self.captions_layout)

        # Download Button
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.download)
        self.button_layout.addWidget(self.download_button)

        # GIF Loading Screen
        self.gif_layout = QHBoxLayout()
        self.main_layout.addLayout(self.gif_layout)

        # Progress Area
        self.count_layout = QHBoxLayout()
        # Create a QListWidget to display downloading status
        self.download_list_widget = ListWidget()
        self.count_layout.addWidget(self.download_list_widget)
        self.main_layout.addLayout(self.count_layout)

        self.setLayout(self.main_layout)
        self.caption_list = None  # Define the caption_list attribute

    def trigger_captions_list(self):
        link = self.link_entry.text()
        if link == "":
            msg = random.choice(msgs)
            w = MessageBox(
                'No URL Found',
                msg,
                self
            )
            w.yesButton.setText('Alright Genius 🤓')
            w.cancelButton.setText('Yeah let me try again 🤝')

            if w.exec():
                pass

        else:
            try:
                youtube_client = YouTube(link)
                captions = youtube_client.captions
                language_names = []
                language_dict = {}

                for caption in captions:
                    language_name = caption.name.split(" - ")[0]  # Extracting the main language name
                    language_code = caption.code.split(".")[0]  # Extracting the main language code

                    if language_name not in language_dict:
                        language_dict[language_name] = language_code

                    if language_name not in language_names:
                        language_names.append(language_name)

                self.caption_label = StrongBodyLabel('Caption Language', self)
                self.captions_layout.addWidget(self.caption_label)
                self.caption_list = QComboBox()
                self.caption_list.addItems(language_names)
                self.captions_layout.addWidget(self.caption_list)

            except pytube.exceptions.RegexMatchError:
                pass

    def download(self):

        link = self.link_entry.text()
        ext = self.ext_menu.currentText()

        title = ""
        try:
            yt = YouTube(link)
            title = yt.title
        except pytube.exceptions.RegexMatchError:
            title = "Untitled"

        # Open file dialog to get save path
        save_path, _ = QFileDialog.getSaveFileName(self, "Save file", title)

        self.downloader_thread = DownloaderThread(
            link=link,
            save_path=save_path,  # Pass the save path here
            dwnld_list_widget=self.download_list_widget,
            main_window=self,
            caption_list=self.caption_list,
            ext=ext
        )
        # self.downloader_thread.download_finished.connect(self.show_download_finished_message)
        self.downloader_thread.start()
