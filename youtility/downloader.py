import json
import os
import random

import pytube.exceptions
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QComboBox, QFileDialog, QHBoxLayout, \
    QSpacerItem, QLabel, QListWidgetItem
from pytube import YouTube
from qfluentwidgets import (LineEdit,
                            StrongBodyLabel, MessageBox, CheckBox, ListWidget)

from consts import msgs, extension

with open("resources/misc/config.json", "r") as themes_file:
    _themes = json.load(themes_file)

theme_color = _themes["theme"]
progressive = _themes["progressive"]


class DownloaderThread(QThread):
    download_finished = pyqtSignal()

    def __init__(self, link, quality, download_captions, copy_thumbnail_link, dwnld_list_widget, quality_menu,
                 loading_label, main_window, save_path, mp3_only, caption_list=None, folder_path=None):
        super().__init__()
        self.link = link
        self.quality = quality
        self.download_captions = download_captions
        self.copy_thumbnail_link = copy_thumbnail_link
        self.caption_list = caption_list
        self.download_list_widget = dwnld_list_widget
        self.quality_menu = quality_menu
        self.loading_label = loading_label
        self.folder_path = folder_path
        self.save_path = save_path
        self.main_window = main_window
        self.mp3_only = mp3_only

    def run(self):

        def get_gif():
            gifs = ["loading.gif", "loading_2.gif"]
            gif = random.choice(gifs)
            gif_path = "resources/misc/" + gif
            return gif_path

        caption_file_path = os.path.join(self.save_path, "captions.xml")

        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_movie = QMovie(get_gif())
        self.loading_label.setMovie(self.loading_movie)

        if not self.mp3_only:
            youtube_client = YouTube(self.link)
            title = youtube_client.title
            youtube_client.streams.filter(file_extension=extension)
            self.list_item = QListWidgetItem(
                "Downloading: " + title)
            self.download_list_widget.addItem(self.list_item)

            # Get available streams for the video
            streams = youtube_client.streams.filter(progressive=False)

            # Get the selected quality option
            choice = self.quality_menu.currentIndex()
            stream = streams[choice]

            # Download the video
            stream.download(self.save_path)
        youtube_client = YouTube(self.link)
        title = youtube_client.title

        if self.mp3_only:
            youtube_client.streams.filter(file_extension=extension)
            self.list_item = QListWidgetItem(
                "Downloading: " + title)
            self.download_list_widget.addItem(self.list_item)

            # Get available streams for the video
            streams = youtube_client.streams.filter(only_audio=True).first()

            streams.download(self.save_path)

        if self.download_captions:
            # Download and save captions if enabled
            captions = youtube_client.captions
            language_dict = {}
            for caption in captions:
                language_name = caption.name.split(" - ")[0]  # Extracting the main language name
                language_code = caption.code.split(".")[0]  # Extracting the main language code

                if language_name not in language_dict:
                    language_dict[language_name] = language_code

            lang_get = self.caption_list.currentText()
            lang = language_dict.get(lang_get)

            caption_dwnld = youtube_client.captions.get_by_language_code(lang)
            caption_dwnld = caption_dwnld.xml_captions

            # Save the caption file in the same directory as the video
            with open(caption_file_path, 'w', encoding="utf-8") as file:
                file.write(caption_dwnld)

        self.download_finished.emit()
        self.list_item.setText((title + " - Downloaded"))


class YoutubeVideo(QWidget):
    def __init__(self):
        super().__init__()

        spacer_item_small = QSpacerItem(0, 10)
        spacer_item_medium = QSpacerItem(0, 20)

        self.setObjectName("Video")

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # YouTube Link Entry
        self.link_layout = QHBoxLayout()
        self.main_layout.addLayout(self.link_layout)
        self.link_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.link_entry = LineEdit(self)
        self.link_entry.textChanged.connect(self.get_quality)
        self.link_entry.setPlaceholderText("Enter YouTube Video Link: ")
        self.link_layout.addWidget(self.link_entry)

        self.main_layout.addSpacerItem(spacer_item_small)

        # Option menu for Quality
        self.quality_layout = QHBoxLayout()
        self.options_layout = QHBoxLayout()
        self.main_layout.addLayout(self.quality_layout)
        self.main_layout.addLayout(self.options_layout)
        self.quality_menu = QComboBox()
        self.quality_menu.setPlaceholderText("Video Quality (Enter link to view)")
        # self.quality_menu.addItems(["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"])
        self.quality_layout.addWidget(self.quality_menu)
        self.options_layout.addSpacerItem(spacer_item_medium)
        self.thumbnail_url_checkbox = CheckBox('Copy Thumbnail Link', self)
        self.audio_only_checkbox = CheckBox('Download Audio Only', self)
        self.captions_checkbox = CheckBox('Download Captions', self)
        self.captions_checkbox.stateChanged.connect(self.trigger_captions_list)

        self.options_group = QGroupBox("Additional Options")
        self.options_group_layout = QVBoxLayout(self.options_group)
        self.options_group_layout.addWidget(self.captions_checkbox)
        self.options_group_layout.addWidget(self.audio_only_checkbox)
        self.options_group_layout.addWidget(self.thumbnail_url_checkbox)
        self.options_layout.addWidget(self.options_group)

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
        self.loading_label = QLabel()
        self.main_layout.addWidget(self.loading_label)

        # Progress Area
        self.count_layout = QHBoxLayout()
        # Create a QListWidget to display downloading status
        self.download_list_widget = ListWidget()
        self.count_layout.addWidget(self.download_list_widget)
        self.main_layout.addLayout(self.count_layout)

        self.setLayout(self.main_layout)
        self.caption_list = None  # Define the caption_list attribute

        # Other initialization code...

    def get_quality(self):
        url = self.link_entry.text()
        try:
            set_progressive = True
            if progressive == "True":
                set_progressive = True
            else:
                set_progressive = False
            youtube = pytube.YouTube(url)
            streams = youtube.streams.filter(progressive=set_progressive)
            self.quality_menu.clear()
            for stream in streams:
                self.quality_menu.addItem(stream.resolution)
                self.quality_menu.setCurrentText("360p")
        except pytube.exceptions.RegexMatchError:
            pass

    def trigger_captions_list(self):
        if self.captions_checkbox.isChecked():
            link = self.link_entry.text()
            if link == "":
                msg = random.choice(msgs)
                w = MessageBox(
                    'No URL Found',
                    msg,
                    self
                )
                self.captions_checkbox.setChecked(False)
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

        else:
            self.caption_list.hide()
            self.caption_label.hide()

    def download(self):
        def get_gif():
            gifs = ["loading.gif", "loading_2.gif"]
            gif = random.choice(gifs)
            gif_path = "resources/misc/" + gif
            return gif_path

        link = self.link_entry.text()
        quality = self.quality_menu.currentText()
        download_captions = self.captions_checkbox.isChecked()
        copy_thumbnail_link = self.thumbnail_url_checkbox.isChecked()
        mp3_only = ""
        if self.audio_only_checkbox.isChecked():
            mp3_only = True
        else:
            mp3_only = False
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
            quality=quality,
            download_captions=download_captions,
            copy_thumbnail_link=copy_thumbnail_link,
            save_path=save_path,  # Pass the save path here
            loading_label=self.loading_label,
            dwnld_list_widget=self.download_list_widget,
            quality_menu=self.quality_menu,
            main_window=self,
            caption_list=self.caption_list,
            mp3_only=mp3_only
        )
        self.downloader_thread.download_finished.connect(self.show_download_finished_message)
        self.downloader_thread.start()

    def show_download_finished_message(self):
        self.loading_label.hide()
