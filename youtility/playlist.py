import os
import random
import re

import pytube.exceptions
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QComboBox, QFileDialog, QHBoxLayout, \
    QSpacerItem, QLabel, QListWidgetItem
from qfluentwidgets import (LineEdit,
                            StrongBodyLabel, MessageBox, CheckBox, ListWidget, TextEdit)
from pytube import Playlist
from consts import msgs, extension
import threading


class DownloaderThread(QThread):
    download_finished = pyqtSignal()

    def __init__(self, link, quality, copy_thumbnail_link, dwnld_list_widget, quality_menu,
                 loading_label, main_window, save_path, progress_text, folder_path=None):
        super().__init__()
        self.link = link
        self.quality = quality
        self.copy_thumbnail_link = copy_thumbnail_link
        self.download_list_widget = dwnld_list_widget
        self.quality_menu = quality_menu
        self.loading_label = loading_label
        self.folder_path = folder_path
        self.save_path = save_path
        self.progress_textbox = progress_text
        self.main_window = main_window

    def run(self):
        def get_gif():
            gifs = ["loading.gif", "loading_2.gif"]
            gif = random.choice(gifs)
            gif_path = "resource/misc/" + gif
            return gif_path


        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_movie = QMovie(get_gif())
        self.loading_label.setMovie(self.loading_movie)

        # loading_animation()

        playlist = Playlist(self.link)
        playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")
        title = playlist.title
        # playlist.streams.filter(file_extension=extension)
        self.list_item = QListWidgetItem(
            "Downloading: " + title)
        self.download_list_widget.addItem(self.list_item)

        # Get the selected quality option
        choice = self.quality_menu.currentIndex()

        # print(len(playlist.video_urls))
        for video in playlist.videos:
            self.progress_textbox.append('Downloading: {} with URL: {}'.format(video.title, video.watch_url))
            self.progress_textbox.append("\n")

            filtered_streams = video.streams.filter(type='video', progressive=False, file_extension='mp4')

            selected_stream = filtered_streams.filter(resolution=self.quality).first()

            selected_stream.download(output_path=self.save_path)

            self.progress_textbox.append('Downloaded: {}'.format(video.title))

        # if self.download_captions:
        #    for video in playlist.videos:
        #        # Download and save captions if enabled
        #        captions = video.captions
        #        language_dict = {}
        #        for caption in captions:
        #           language_name = caption.name.split(" - ")[0]  # Extracting the main language name
        #          language_code = caption.code.split(".")[0]  # Extracting the main language code
        #
        #                   if language_name not in language_dict:
        #                      language_dict[language_name] = language_code
        #
        #              lang = language_dict.get(lang_get)
        #
        #               caption_dwnld = video.captions.get_by_language_code(lang)
        #              caption_dwnld = caption_dwnld.xml_captions
        #
        #               # Save the caption file in the same directory as the video
        #              with open(caption_file_path, 'w', encoding="utf-8") as file:
        #                 file.write(caption_dwnld)

        self.download_finished.emit()
        self.list_item.setText((title + " - Downloaded"))


class YoutubePlaylist(QWidget):
    def __init__(self):
        super().__init__()

        spacer_item_small = QSpacerItem(0, 10)
        spacer_item_medium = QSpacerItem(0, 20)

        self.setObjectName("Playlist")

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # YouTube Link Entry
        self.link_layout = QHBoxLayout()
        self.main_layout.addLayout(self.link_layout)
        self.link_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.link_entry = LineEdit(self)
        self.link_entry.textChanged.connect(self.get_quality)
        self.link_entry.setPlaceholderText("Enter YouTube Playlist Link: ")
        self.link_layout.addWidget(self.link_entry)

        self.main_layout.addSpacerItem(spacer_item_small)

        # Option menu for Quality
        self.quality_layout = QHBoxLayout()
        self.options_layout = QHBoxLayout()
        self.main_layout.addLayout(self.quality_layout)
        self.main_layout.addLayout(self.options_layout)
        self.quality_menu = QComboBox()
        self.quality_menu.setPlaceholderText("Video Quality (Applies to all videos)")
        self.quality_menu.addItems(["1080p", "720p", "480p", "360p", "240p", "144p"])
        self.quality_layout.addWidget(self.quality_menu)
        self.options_layout.addSpacerItem(spacer_item_medium)
        self.thumbnail_url_checkbox = CheckBox('Copy Thumbnail URL', self)

        self.options_group = QGroupBox("Additional Options")
        self.options_group_layout = QVBoxLayout(self.options_group)
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
        self.download_list_text = TextEdit()
        self.count_layout.addWidget(self.download_list_widget)
        self.count_layout.addWidget(self.download_list_text)
        self.main_layout.addLayout(self.count_layout)

        self.setLayout(self.main_layout)
        self.caption_list = None  # Define the caption_list attribute

        # Other initialization code...

    def get_quality(self):
        url = self.link_entry.text()
        try:
            youtube = pytube.YouTube(url)
            streams = youtube.streams.filter(progressive=False)
            self.quality_menu.clear()
            for stream in streams:
                self.quality_menu.addItem(stream.resolution)
                self.quality_menu.setCurrentText("360p")
        except pytube.exceptions.RegexMatchError:
            pass

    def download(self):
        def get_gif():
            gifs = ["loading.gif", "loading_2.gif"]
            gif = random.choice(gifs)
            gif_path = "resource/misc/" + gif
            return gif_path

        link = self.link_entry.text()
        quality = self.quality_menu.currentText()
        copy_thumbnail_link = self.thumbnail_url_checkbox.isChecked()
        title = ""
        try:
            yt = Playlist(link)
            title = yt.title
        except pytube.exceptions.RegexMatchError:
            title = "Untitled"

        # Open file dialog to get save path
        save_path, _ = QFileDialog.getSaveFileName(self, "Save file", title)

        self.downloader_thread = DownloaderThread(
            link=link,
            quality=quality,
            copy_thumbnail_link=copy_thumbnail_link,
            save_path=save_path,  # Pass the save path here
            loading_label=self.loading_label,
            dwnld_list_widget=self.download_list_widget,
            quality_menu=self.quality_menu,
            main_window=self,
            progress_text=self.download_list_text
        )
        self.downloader_thread.download_finished.connect(self.show_download_finished_message)
        self.downloader_thread.start()

    def show_download_finished_message(self):
        self.loading_label.hide()
