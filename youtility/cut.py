import yt_dlp
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, \
    QSpacerItem, QLabel, QFileDialog
from pytube import YouTube
from qfluentwidgets import (LineEdit,
                            ListWidget, PushButton, MessageBox)
from yt_dlp.utils import download_range_func


class DownloaderThread(QThread):
    download_finished = pyqtSignal()
    on_progress = pyqtSignal(int)

    def __init__(self, link, start_time, end_time, save_path):
        super().__init__()
        self.link = link
        self.start_time = start_time
        self.end_time = end_time
        self.save_path = save_path

    def download(self):
        yt_opts = {
            'outtmpl': self.save_path,
            'verbose': True,
            'download_ranges': download_range_func(None, [(self.start_time, self.end_time)]),
            'force_keyframes_at_cuts': True,
        }
        try:
            if self.start_time <= self.end_time:
                with yt_dlp.YoutubeDL(yt_opts) as ydl:
                    ydl.download(self.link)

            elif self.start_time > self.end_time:
                w = MessageBox(
                    "ERROR",
                    "Start time cannot be greater than end time")
                w.yesButton.setText('Alright!')
                w.cancelButton.setText('ALRIGHT!, but in CAPS LOCK')
                if w.exec():
                    pass
        except:
            w = MessageBox(
                "ERROR",
                "Unexpected Error Occurred")
            w.yesButton.setText('Hmm OK!')
            w.cancelButton.setText('Let me try again')
            if w.exec():
                pass

    def init_timers(self):
        try:
            import yt_dlp

            ydl_opts = {}
            length = ""

            video = YouTube(self.link)
            length = video.length
            length = self.seconds_to_hhmmss(length)
            self.end_time.setText(length)
        except:
            pass

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

        # Download Button
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.download_button = PushButton()
        self.download_button.setText("Cut & Download")
        self.download_button.clicked.connect(self.download)
        self.button_layout.addWidget(self.download_button)

        # GIF Loading Screen
        self.gif_layout = QHBoxLayout()
        self.main_layout.addLayout(self.gif_layout)
        self.loading_label = QLabel()
        self.main_layout.addWidget(self.loading_label)

        self.count_layout = QHBoxLayout()
        self.download_list_widget = ListWidget()
        self.count_layout.addWidget(self.download_list_widget)
        self.main_layout.addLayout(self.count_layout)

        self.setLayout(self.main_layout)
        self.caption_list = None

    def download(self):
        link = self.link_entry.text()
        start_time = self.hhmmss_to_seconds(self.start_time.text())
        end_time = self.hhmmss_to_seconds(self.end_time.text())

        save_path, _ = QFileDialog.getSaveFileName(self, "Save file", "cut_video")

        self.download_thread = DownloaderThread(link, start_time, end_time, save_path)
        self.download_thread.finished.connect(self.show_download_finished_message)

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
        except:
            pass

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
