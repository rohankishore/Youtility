import logging
import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, \
    QSpacerItem, QLabel, QFileDialog
from pytube import YouTube
from qfluentwidgets import (LineEdit,
                            ListWidget, PushButton, MessageBox, ProgressBar, TextEdit)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class Stream(QObject):
    new_text = pyqtSignal(str)

    def write(self, text):
        self.new_text.emit(str(text))

    def flush(self):
        pass


class DownloaderThread(QThread):
    download_finished = pyqtSignal()
    new_text = pyqtSignal(str)

    def __init__(self, link, start_time, end_time, save_path):
        super().__init__()
        self.link = link
        self.start_time = start_time
        self.end_time = end_time
        self.save_path = save_path
        self.stream = Stream()
        self.stream.new_text.connect(self.handle_new_text)

    def run(self):
        link = self.link
        start_time = self.hhmmss_to_seconds(self.start_time)
        end_time = self.hhmmss_to_seconds(self.end_time)

        import yt_dlp
        from yt_dlp.utils import download_range_func

        yt_opts = {
            'outtmpl': self.save_path,
            'verbose': True,
            'download_ranges': download_range_func(None, [(start_time, end_time)]),
            'force_keyframes_at_cuts': True,
        }

        # Redirect stdout and stderr
        sys.stdout = self.stream
        sys.stderr = self.stream

        try:
            if start_time <= end_time:
                with yt_dlp.YoutubeDL(yt_opts) as ydl:
                    ydl.download([link])

                self.download_finished.emit()
            else:
                self.show_message_box("ERROR", "Start time cannot be greater than end time")
        except Exception as e:
            self.show_message_box("ERROR", f"Unexpected Error Occurred: {e}")

        # Reset stdout and stderr to their original state
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def handle_new_text(self, text):
        self.new_text.emit(text)

    def show_message_box(self, title, message):
        w = MessageBox(title, message)
        w.yesButton.setText('OK')
        w.exec()

    def hhmmss_to_seconds(self, hhmmss):
        h, m, s = map(int, hhmmss.split(':'))
        return h * 3600 + m * 60 + s

    def seconds_to_hhmmss(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02}"


class CutVideos(QWidget):
    def __init__(self):
        super().__init__()

        spacer_item_small = QSpacerItem(0, 10)
        spacer_item_medium = QSpacerItem(0, 20)

        self.setObjectName("Cut")

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # YouTube Link Entry
        self.link_layout = QHBoxLayout()
        self.main_layout.addLayout(self.link_layout)
        self.link_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.link_entry = LineEdit(self)
        self.link_entry.textChanged.connect(self.init_timers)
        self.link_entry.setPlaceholderText("Enter YouTube Video Link: ")
        self.link_layout.addWidget(self.link_entry)

        self.main_layout.addSpacerItem(spacer_item_small)

        self.time_layout = QHBoxLayout()
        self.main_layout.addLayout(self.time_layout)
        self.start_time = LineEdit()
        self.start_time.setPlaceholderText("Start Time")
        self.start_time.setText("00:00:00")
        self.end_time = LineEdit()
        self.end_time.setPlaceholderText("End Time")

        self.time_layout.addWidget(self.start_time)
        self.time_layout.addWidget(self.end_time)

        self.main_layout.addSpacerItem(spacer_item_medium)

        self.main_layout.addSpacerItem(spacer_item_medium)

        # Console Output
        self.console_output = TextEdit()
        self.console_output.setReadOnly(True)
        self.main_layout.addWidget(self.console_output)

        self.main_layout.addSpacerItem(spacer_item_medium)

        # Download Button
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.download_button = PushButton()
        self.download_button.setText("Cut & Download")
        self.download_button.clicked.connect(self.download)
        self.button_layout.addWidget(self.download_button)

        self.loading_label = QLabel()
        self.main_layout.addWidget(self.loading_label)

        self.main_layout.addSpacerItem(spacer_item_medium)
        self.main_layout.addSpacerItem(spacer_item_medium)
        self.main_layout.addSpacerItem(spacer_item_medium)
        self.main_layout.addSpacerItem(spacer_item_medium)

        disclaimer = QLabel("<b>***</b> <b><i> This feature uses YT-DLP and requires <a href='https://ffmpeg.org/download.html'>ffmpeg</a> and will take slightly longer time to render, and the quality is also NOT adjustable.</i></b>")
        self.main_layout.addWidget(disclaimer)

        self.count_layout = QHBoxLayout()
        self.download_list_widget = ListWidget()
        self.count_layout.addWidget(self.download_list_widget)
        self.main_layout.addLayout(self.count_layout)

        self.setLayout(self.main_layout)
        self.caption_list = None

    def download(self):
        link = self.link_entry.text()
        start_time = (self.start_time.text())
        end_time = (self.end_time.text())

        save_path, _ = QFileDialog.getSaveFileName(self, "Save file", "cut_video")

        if save_path:
            thread = DownloaderThread(link, start_time, end_time, save_path)
            thread.download_finished.connect(self.show_download_finished_message)
            thread.new_text.connect(self.append_text)
            thread.start()

    @pyqtSlot(str)
    def append_text(self, text):
        logging.debug(f"Appending text: {text}")
        self.console_output.append(text)

    def init_timers(self):
        link = self.link_entry.text()
        try:
            import yt_dlp

            ydl_opts = {}
            length = ""

            video = YouTube(link)
            length = (video.length)
            length = self.seconds_to_hhmmss(length)
            self.end_time.setText(length)
        except Exception as e:
            logging.error(f"Failed to initialize timers: {e}", exc_info=True)

    def hhmmss_to_seconds(self, hhmmss):
        h, m, s = map(int, hhmmss.split(':'))
        return h * 3600 + m * 60 + s

    def seconds_to_hhmmss(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02}"

    def show_download_finished_message(self):
        self.loading_label.hide()
