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

    def __init__(self, link, quality, dwnld_list_widget, quality_menu,
                 loading_label, main_window, save_path, progress_text, mp3_only, folder_path=None, copy_thumbnail_link=None):
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
        self.mp3_only = mp3_only

    def run(self):
        def get_gif():
            gifs = ["loading.gif", "loading_2.gif"]
            gif = random.choice(gifs)
            gif_path = "resource/misc/" + gif
            return gif_path

        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_movie = QMovie(get_gif())
        self.loading_label.setMovie(self.loading_movie)

        playlist = Playlist(self.link)
        playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")
        title = playlist.title
        self.list_item = QListWidgetItem(
            "Downloading: " + title)
        self.download_list_widget.addItem(self.list_item)

        choice = self.quality_menu.currentIndex()

        for video in playlist.videos:
            if not self.mp3_only:
                self.progress_textbox.append('Downloading: {} with URL: {}'.format(video.title, video.watch_url))
                self.progress_textbox.append("\n")

                filtered_streams = video.streams.filter(type='video', progressive=False, file_extension='mp4')

                selected_stream = filtered_streams.filter(resolution=self.quality).first()

                selected_stream.download(output_path=self.save_path)

                self.progress_textbox.append('Downloaded: {}'.format(video.title))

            elif self.mp3_only:
                self.progress_textbox.append('Downloading: {} with URL: {}'.format((video.title+" -audio"), video.watch_url))
                self.progress_textbox.append("\n")

                filtered_streams = video.streams.filter(only_audio=True).first()

                # selected_stream = filtered_streams.filter(only_audio=True).first()

                filtered_streams.download(output_path=self.save_path)

                self.progress_textbox.append('Downloaded: {}'.format(video.title))

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
        self.audio_only_checkbox = CheckBox('Download Audio Only', self)

        self.options_group = QGroupBox("Additional Options")
        self.options_group_layout = QVBoxLayout(self.options_group)
        self.options_group_layout.addWidget(self.thumbnail_url_checkbox)
        self.options_group_layout.addWidget(self.audio_only_checkbox)
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
        self.download_list_text.setReadOnly(True)
        self.count_layout.addWidget(self.download_list_widget)
        self.count_layout.addWidget(self.download_list_text)
        self.main_layout.addLayout(self.count_layout)

        self.setLayout(self.main_layout)
        self.caption_list = None

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
        link = self.link_entry.text()
        quality = self.quality_menu.currentText()
        mp3_only = ""
        if self.audio_only_checkbox.isChecked():
            mp3_only = True
        else:
            mp3_only = False

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
            save_path=save_path,  # Pass the save path here
            loading_label=self.loading_label,
            dwnld_list_widget=self.download_list_widget,
            quality_menu=self.quality_menu,
            main_window=self,
            progress_text=self.download_list_text,
            mp3_only=mp3_only
        )
        self.downloader_thread.download_finished.connect(self.show_download_finished_message)
        self.downloader_thread.start()

    def show_download_finished_message(self):
        self.loading_label.hide()
