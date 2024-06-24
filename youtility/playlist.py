import json
import os
import random
import re
import subprocess

import pytube.exceptions
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QComboBox, QFileDialog, QHBoxLayout, \
    QSpacerItem, QLabel, QListWidgetItem
from pytube import Playlist
from qfluentwidgets import (LineEdit,
                            CheckBox, ListWidget, TextEdit, PushButton, ComboBox)

with open("resources/misc/config.json", "r") as themes_file:
    _themes = json.load(themes_file)

progressive = _themes["progressive"]


class DownloaderThread(QThread):
    download_finished = pyqtSignal()

    def __init__(self, link, quality, dwnld_list_widget, quality_menu,
                 loading_label, main_window, save_path, progress_text, mp3_only, filename, audio_format, folder_path=None,
                 copy_thumbnail_link=None):
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
        self.audio_format = audio_format
        self.filename = filename

    def run(self):
        def get_gif():
            gifs = ["loading.gif", "loading_2.gif"]
            gif = random.choice(gifs)
            gif_path = "resources/misc/" + gif
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
                self.progress_textbox.append(
                    'Downloading: {} with URL: {}'.format((video.title + " -audio"), video.watch_url))
                self.progress_textbox.append("\n")
                filtered_streams = video.streams.filter(only_audio=True).first()
                filtered_streams.download(output_path=self.save_path, filename=(video.title + ".mp3"))
                self.progress_textbox.append('Downloaded: {}'.format(video.title))

                if self.audio_format == "FLAC":
                    input_file = os.path.join(self.save_path, (video.title + ".mp3")).replace("\\", "/")
                    output_file = os.path.join(self.save_path, (video.title + ".flac")).replace("\\", "/")

                    # Run the ffmpeg command to convert mp4 to flac
                    ffmpeg_command = f'ffmpeg -i "{input_file}" "{output_file}"'
                    try:
                        subprocess.run(ffmpeg_command, shell=True, check=True)
                        os.remove(input_file)
                    except subprocess.CalledProcessError as e:
                        print(f"Error during conversion: {e}")
                        self.list_item.setText((title + " - Download failed during conversion"))

        self.download_finished.emit()
        self.list_item.setText((title + " - Downloaded"))


class YoutubePlaylist(QWidget):
    def __init__(self):
        super().__init__()

        spacer_item_small = QSpacerItem(0, 10)
        spacer_item_medium = QSpacerItem(0, 20)

        self.setObjectName("Playlist")
        self.audio_format_choice = ComboBox()

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
        self.quality_menu = ComboBox()
        self.quality_menu.setPlaceholderText("Video Quality (Applies to all videos)")
        if progressive == "True":
            self.quality_menu.addItems(["720p", "480p", "360p", "240p", "144p"])
        else:
            self.quality_menu.addItems(["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"])
        self.quality_layout.addWidget(self.quality_menu)
        self.options_layout.addSpacerItem(spacer_item_medium)
        self.thumbnail_url_checkbox = CheckBox('Copy Thumbnail URL', self)
        self.audio_only_checkbox = CheckBox('Download Audio Only', self)
        self.audio_only_checkbox.stateChanged.connect(self.audio_format_init)

        self.options_group = QGroupBox("Additional Options")
        self.options_group_layout = QVBoxLayout(self.options_group)
        self.options_group_layout.addWidget(self.thumbnail_url_checkbox)
        self.options_group_layout.addWidget(self.audio_only_checkbox)
        self.options_group_layout.addSpacerItem(spacer_item_medium)
        self.options_layout.addWidget(self.options_group)

        self.main_layout.addSpacerItem(spacer_item_small)

        self.captions_layout = QHBoxLayout()
        self.captions_layout.addSpacerItem(spacer_item_medium)
        self.main_layout.addLayout(self.captions_layout)

        # Download Button
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.download_button = PushButton()
        self.download_button.setText("Download")
        self.download_button.clicked.connect(self.download)
        self.button_layout.addWidget(self.download_button)

        self.loading_label = QLabel()
        self.main_layout.addWidget(self.loading_label)

        self.count_layout = QHBoxLayout()
        self.download_list_widget = ListWidget()
        self.download_list_text = TextEdit()
        self.download_list_text.setReadOnly(True)
        self.count_layout.addWidget(self.download_list_widget)
        self.count_layout.addWidget(self.download_list_text)
        self.main_layout.addLayout(self.count_layout)

        self.setLayout(self.main_layout)
        self.caption_list = None

    def audio_format_init(self):
        if self.audio_only_checkbox.isChecked():
            audio_formats = ["MP3", "FLAC"]
            self.audio_format_choice = ComboBox()
            self.audio_format_choice.setCurrentText(_themes["def-audio-format"])
            self.audio_format_choice.addItems(audio_formats)
            self.options_group_layout.addWidget(self.audio_format_choice)
        else:
            self.audio_format_choice.hide()

    def get_quality(self):
        url = self.link_entry.text()
        set_progressive = True
        try:
            youtube = pytube.YouTube(url)
            if progressive == "True":
                set_progressive = True
            else:
                set_progressive = False
            streams = youtube.streams.filter(progressive=set_progressive)
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

        audio_format = self.audio_format_choice.currentText()
        save_path, _ = QFileDialog.getSaveFileName(self, "Save file", title)
        filename = os.path.basename(save_path)
        filename_without_extension, _ = os.path.splitext(filename)

        self.downloader_thread = DownloaderThread(
            link=link,
            quality=quality,
            save_path=save_path,  # Pass the save path here
            loading_label=self.loading_label,
            dwnld_list_widget=self.download_list_widget,
            quality_menu=self.quality_menu,
            main_window=self,
            progress_text=self.download_list_text,
            mp3_only=mp3_only,
            audio_format=audio_format,
            filename=filename_without_extension
        )
        self.downloader_thread.download_finished.connect(self.show_download_finished_message)
        self.downloader_thread.start()

    def show_download_finished_message(self):
        self.loading_label.hide()
