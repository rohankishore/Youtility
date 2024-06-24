import json
import os
import random
import subprocess
import threading
import sys
import pytube.exceptions
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QComboBox, QFileDialog, QHBoxLayout, \
    QSpacerItem, QLabel, QListWidgetItem, QProgressBar
from pytube import YouTube
from qfluentwidgets import (LineEdit,
                            StrongBodyLabel, MessageBox, CheckBox, ListWidget, PushButton, ComboBox, ProgressBar)

from consts import msgs, extension

with open("resources/misc/config.json", "r") as themes_file:
    _themes = json.load(themes_file)

theme_color = _themes["theme"]
progressive = _themes["progressive"]


class DownloaderThread(QThread):
    download_finished = pyqtSignal()
    progress_update = pyqtSignal(int)

    def __init__(self, link, quality, download_captions, copy_thumbnail_link, dwnld_list_widget, quality_menu,
                 loading_label, main_window, save_path, mp3_only, audio_format, filename, caption_list=None, folder_path=None):
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
        self.audio_format = audio_format
        self.file_size = 0
        self.filename = filename

    def run(self):
        caption_file_path = os.path.join(self.save_path, "captions.xml")

        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        youtube_client = YouTube(self.link, on_progress_callback=self.progress_function)
        title = youtube_client.title
        self.list_item = QListWidgetItem("Downloading: " + title)
        self.download_list_widget.addItem(self.list_item)

        if not self.mp3_only:
            youtube_client.streams.filter(file_extension=extension)

            # Get available streams for the video
            streams = youtube_client.streams.filter(progressive=False)

            # Get the selected quality option
            choice = self.quality_menu.currentIndex()
            stream = streams[choice]

            self.file_size = stream.file_size

            # Download the video
            stream.download(self.save_path)

        else:
            youtube_client.streams.filter(file_extension='mp4')  # Use your specific extension
            stream = youtube_client.streams.filter(only_audio=True).first()
            self.file_size = stream.filesize  # Set the file size
            stream.download(output_path=self.save_path, filename=self.filename + ".mp3")

            # Conversion to FLAC using ffmpeg
            if self.audio_format == "FLAC":
                input_file = os.path.join(self.save_path, self.filename + ".mp3").replace("\\", "/")
                output_file = os.path.join(self.save_path, self.filename + ".flac").replace("\\", "/")

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

        if self.download_captions:
            # Download and save captions if enabled
            captions = youtube_client.captions
            language_dict = {}
            for caption in captions:
                language_name = caption.name.split(" - ")[0]
                language_code = caption.code.split(".")[0]

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

    def progress_function(self, chunk, file_handle, bytes_remaining):
        current = ((self.file_size - bytes_remaining) / self.file_size)
        percent = int(current * 100)
        self.progress_update.emit(percent)


class YoutubeVideo(QWidget):
    def __init__(self):
        super().__init__()

        spacer_item_small = QSpacerItem(0, 10)
        spacer_item_medium = QSpacerItem(0, 20)

        self.setObjectName("Video")
        self.audio_only_checkbox = ""

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
        self.quality_menu = ComboBox()
        self.quality_menu.setPlaceholderText("Video Quality (Enter link to view)")
        # self.quality_menu.addItems(["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"])
        self.quality_layout.addWidget(self.quality_menu)

        self.options_layout.addSpacerItem(spacer_item_medium)
        self.thumbnail_url_checkbox = CheckBox('Copy Thumbnail Link', self)

        self.audio_only_checkbox = CheckBox('Download Audio Only', self)
        self.audio_only_checkbox.stateChanged.connect(self.update_audio_format)

        self.captions_checkbox = CheckBox('Download Captions', self)
        self.captions_checkbox.stateChanged.connect(self.trigger_captions_list)

        self.options_group = QGroupBox("Additional Options")
        self.options_group_layout = QVBoxLayout(self.options_group)
        self.options_group_layout.addWidget(self.captions_checkbox)
        self.options_group_layout.addWidget(self.audio_only_checkbox)
        self.options_group_layout.addWidget(self.thumbnail_url_checkbox)
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

        # GIF Loading Screen
        self.gif_layout = QHBoxLayout()
        self.main_layout.addLayout(self.gif_layout)
        self.loading_label = QLabel()
        self.main_layout.addWidget(self.loading_label)

        # Progress Bar
        self.progress_bar = ProgressBar(self)
        self.main_layout.addWidget(self.progress_bar)
        self.progress_bar.hide()  # Initially hide the progress bar

        # Progress Area
        self.count_layout = QHBoxLayout()
        # Create a QListWidget to display downloading status
        self.download_list_widget = ListWidget()
        self.count_layout.addWidget(self.download_list_widget)
        self.main_layout.addLayout(self.count_layout)

        self.setLayout(self.main_layout)
        self.caption_list = None  # Define the caption_list attribute

    def update_audio_format(self):
        audio_formats = ["MP3", "FLAC"]
        if self.audio_only_checkbox.isChecked():
            self.audio_format_select = ComboBox()
            self.audio_format_select.addItems(audio_formats)
            self.options_group_layout.addWidget(self.audio_format_select)
        else:
            self.audio_format_select.hide()

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
        def trigger_captions():
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
                        self.caption_list = ComboBox()
                        self.caption_list.addItems(language_names)
                        self.captions_layout.addWidget(self.caption_list)

                    except pytube.exceptions.RegexMatchError:
                        pass

            else:
                self.caption_list.hide()
                self.caption_label.hide()

        thread = threading.Thread(target=trigger_captions)
        thread.start()

    def download(self):
        link = self.link_entry.text()
        quality = self.quality_menu.currentText()
        download_captions = self.captions_checkbox.isChecked()
        copy_thumbnail_link = self.thumbnail_url_checkbox.isChecked()
        mp3_only = ""
        audio_format = "MP3"
        if self.audio_only_checkbox.isChecked():
            mp3_only = True
            audio_format = self.audio_format_select.currentText()
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
        if not save_path:
            return

        # Extract filename from save_path
        filename = os.path.basename(save_path)
        filename_without_extension, _ = os.path.splitext(filename)

        self.downloader_thread = DownloaderThread(
            link=link,
            quality=quality,
            download_captions=download_captions,
            copy_thumbnail_link=copy_thumbnail_link,
            save_path=os.path.dirname(save_path),  # Pass the directory path here
            filename=filename_without_extension,  # Pass the filename without extension
            loading_label=self.loading_label,
            dwnld_list_widget=self.download_list_widget,
            quality_menu=self.quality_menu,
            main_window=self,
            caption_list=self.caption_list,
            mp3_only=mp3_only,
            audio_format=audio_format
        )
        self.downloader_thread.download_finished.connect(self.show_download_finished_message)
        self.downloader_thread.progress_update.connect(self.update_progress_bar)
        self.progress_bar.show()
        self.downloader_thread.start()

    def show_download_finished_message(self):
        self.loading_label.setText("Download Finished")
        #self.progress_bar.hide()

    def update_progress_bar(self, percent):
        self.progress_bar.setValue(percent)