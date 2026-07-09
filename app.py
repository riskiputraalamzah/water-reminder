import os
import sys
import signal

from PIL import Image, ImageSequence

from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QStyle,
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QMovie

from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    """
    Supaya tetap aman saat dijalankan sebagai .py biasa
    maupun saat nanti dibuild jadi .exe pakai PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)

    return os.path.join(BASE_DIR, relative_path)


GIF_PATH = resource_path("target_transparent.gif")


# =========================
# FINAL CONFIG
# =========================

# Reminder normal: 30 menit
NORMAL_INTERVAL_MS = 30 * 60 * 1000

# Snooze: 10 menit
SNOOZE_INTERVAL_MS = 10 * 60 * 1000

# Untuk testing cepat, sementara bisa aktifkan ini:
# NORMAL_INTERVAL_MS = 30 * 1000
# SNOOZE_INTERVAL_MS = 10 * 1000

DISPLAY_WIDTH = 600

HOLD_FRAME = 50
WALK_OUT_FRAME = 130

DEBUG_FRAMES = False

CELEBRATION_DURATION_MS = 2000
SNOOZE_WARNING_DURATION_MS = 3000

# Warning mulai muncul pada snooze ke-3 dan seterusnya
SNOOZE_WARNING_THRESHOLD = 3

# Saat app auto-run di startup, lebih enak jangan langsung muncul.
# Dia akan mulai menghitung 30 menit dulu.
SHOW_ON_START = False

# untuk debug
# SHOW_ON_START = True


def get_gif_info(gif_path):
    gif = Image.open(gif_path)

    frame_count = 0
    total_duration = 0

    for frame in ImageSequence.Iterator(gif):
        frame_count += 1
        total_duration += frame.info.get("duration",
                                         gif.info.get("duration", 100))

    width, height = gif.size

    return {
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "duration": total_duration,
    }


class WaterReminderWindow(QWidget):
    def __init__(self, gif_path, on_finish):
        super().__init__()

        self.gif_path = gif_path
        self.on_finish = on_finish

        self.gif_info = get_gif_info(self.gif_path)
        self.total_frames = self.gif_info["frame_count"]
        self.end_frame = self.total_frames - 1

        self.state = "idle"

        # Jumlah snooze berturut-turut sejak terakhir klik "Sudah minum"
        self.snooze_count = 0

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setAttribute(Qt.WA_TranslucentBackground)

        self.main_layout.addWidget(self.label)

        self.movie = QMovie(self.gif_path)
        self.movie.setCacheMode(QMovie.CacheAll)

        original_width = self.gif_info["width"]
        original_height = self.gif_info["height"]

        display_height = int(DISPLAY_WIDTH * original_height / original_width)

        self.display_size = QSize(DISPLAY_WIDTH, display_height)

        self.movie.setScaledSize(self.display_size)
        self.movie.frameChanged.connect(self.on_frame_changed)

        self.label.setFixedSize(self.display_size)
        self.label.setMovie(self.movie)

        self.resize(DISPLAY_WIDTH, display_height)

        self.create_question_box()
        self.create_celebration_box()
        self.create_snooze_warning_box()

        self.move_to_bottom_right()

    def create_question_box(self):
        self.question_box = QWidget(self)
        self.question_box.setFixedSize(360, 140)

        self.question_box.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid rgba(30, 30, 30, 180);
                border-radius: 18px;
            }

            QLabel {
                color: #222222;
                font-size: 16px;
                font-weight: bold;
                border: none;
                background: transparent;
            }

            QPushButton {
                background-color: #2563eb;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 8px 12px;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton#snoozeButton {
                background-color: #f59e0b;
                color: white;
            }

            QPushButton#snoozeButton:hover {
                background-color: #d97706;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        self.question_box.setLayout(layout)

        text = QLabel("Sudah minum air sekarang?")
        text.setAlignment(Qt.AlignCenter)
        layout.addWidget(text)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.drink_button = QPushButton("Sudah minum")
        self.snooze_button = QPushButton("Snooze 10 menit")
        self.snooze_button.setObjectName("snoozeButton")

        self.drink_button.clicked.connect(self.handle_drink_now)
        self.snooze_button.clicked.connect(self.handle_snooze)

        button_layout.addWidget(self.drink_button)
        button_layout.addWidget(self.snooze_button)

        layout.addLayout(button_layout)

        self.question_box.hide()

    def create_celebration_box(self):
        self.celebration_box = QWidget(self)
        self.celebration_box.setFixedSize(340, 90)

        self.celebration_box.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 245);
                border: 2px solid rgba(34, 197, 94, 220);
                border-radius: 18px;
            }

            QLabel {
                color: #16a34a;
                font-size: 18px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        self.celebration_box.setLayout(layout)

        text = QLabel("Horeee! 🎉\nLanjutkan minumnya dulu.")
        text.setAlignment(Qt.AlignCenter)
        layout.addWidget(text)

        self.celebration_box.hide()

    def create_snooze_warning_box(self):
        self.snooze_warning_box = QWidget(self)
        self.snooze_warning_box.setFixedSize(420, 125)

        self.snooze_warning_box.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 247, 237, 245);
                border: 2px solid rgba(249, 115, 22, 230);
                border-radius: 18px;
            }

            QLabel {
                color: #9a3412;
                font-size: 15px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        self.snooze_warning_box.setLayout(layout)

        self.snooze_warning_label = QLabel("")
        self.snooze_warning_label.setAlignment(Qt.AlignCenter)
        self.snooze_warning_label.setWordWrap(True)

        layout.addWidget(self.snooze_warning_label)

        self.snooze_warning_box.hide()

    def position_overlays(self):
        qx = (self.width() - self.question_box.width()) // 2
        qy = 20
        self.question_box.move(qx, qy)

        cx = (self.width() - self.celebration_box.width()) // 2
        cy = 20
        self.celebration_box.move(cx, cy)

        wx = (self.width() - self.snooze_warning_box.width()) // 2
        wy = 20
        self.snooze_warning_box.move(wx, wy)

    def move_to_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()

        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 20

        self.move(x, y)

    def play_reminder(self):
        if self.state != "idle":
            return

        self.state = "walking_in"

        self.position_overlays()
        self.question_box.hide()
        self.celebration_box.hide()
        self.snooze_warning_box.hide()

        self.move_to_bottom_right()

        self.show()
        self.raise_()
        self.activateWindow()

        self.movie.stop()
        self.movie.jumpToFrame(0)
        self.movie.start()

    def on_frame_changed(self, frame_number):
        if DEBUG_FRAMES:
            print(
                f"Frame: {frame_number} / {self.end_frame} | State: {self.state}")

        if self.state == "walking_in":
            if frame_number >= HOLD_FRAME:
                self.pause_at_question()

        elif self.state in ["drinking", "walking_out_snooze"]:
            if frame_number >= self.end_frame:
                self.finish_animation()

    def pause_at_question(self):
        self.state = "waiting_answer"

        self.movie.setPaused(True)

        self.question_box.show()
        self.question_box.raise_()

    def handle_drink_now(self):
        if self.state != "waiting_answer":
            return

        # User sudah minum, jadi snooze berturut-turut direset
        self.snooze_count = 0

        self.question_box.hide()

        self.movie.setPaused(True)

        self.state = "celebration_before_drinking"

        self.celebration_box.show()
        self.celebration_box.raise_()

        QTimer.singleShot(
            CELEBRATION_DURATION_MS,
            self.start_drinking_animation
        )

    def start_drinking_animation(self):
        if self.state != "celebration_before_drinking":
            return

        self.celebration_box.hide()

        self.state = "drinking"

        self.movie.setPaused(False)
        self.movie.start()

    def handle_snooze(self):
        if self.state != "waiting_answer":
            return

        self.snooze_count += 1

        self.question_box.hide()

        # Saat snooze, jangan lanjut minum.
        # Tahan dulu di frame saat ini.
        self.movie.setPaused(True)

        if self.snooze_count >= SNOOZE_WARNING_THRESHOLD:
            self.show_snooze_warning()
        else:
            self.start_snooze_walkout()

    def show_snooze_warning(self):
        self.state = "snooze_warning"

        estimated_minutes = 30 + (self.snooze_count * 10)

        if self.snooze_count == SNOOZE_WARNING_THRESHOLD:
            message = (
                f"Ini sudah snooze ke-{self.snooze_count} 😅\n"
                f"Berarti kurang lebih sudah {estimated_minutes} menit sejak reminder utama.\n"
                "Yuk, jangan ditunda terus. Minum air sebentar aja."
            )
        else:
            message = (
                f"Snooze ke-{self.snooze_count} nih 😅\n"
                f"Kurang lebih sudah {estimated_minutes} menit sejak reminder utama.\n"
                "Tubuhmu tetap butuh air. Jangan lupa minum ya."
            )

        self.snooze_warning_label.setText(message)

        self.snooze_warning_box.show()
        self.snooze_warning_box.raise_()

        QTimer.singleShot(
            SNOOZE_WARNING_DURATION_MS,
            self.start_snooze_walkout
        )

    def start_snooze_walkout(self):
        if self.state not in ["waiting_answer", "snooze_warning"]:
            return

        self.snooze_warning_box.hide()

        self.state = "walking_out_snooze"

        self.movie.setPaused(False)

        if 0 <= WALK_OUT_FRAME < self.total_frames:
            self.movie.jumpToFrame(WALK_OUT_FRAME)

        self.movie.start()

    def finish_animation(self):
        self.movie.stop()

        if self.state == "drinking":
            # Setelah benar-benar minum, balik ke pola normal 30 menit
            self.close_and_schedule(NORMAL_INTERVAL_MS)

        elif self.state == "walking_out_snooze":
            # Setelah snooze, tetap mengacu ke snooze 10 menit
            self.close_and_schedule(SNOOZE_INTERVAL_MS)

        else:
            self.close_and_schedule(NORMAL_INTERVAL_MS)

    def close_and_schedule(self, next_delay_ms):
        self.question_box.hide()
        self.celebration_box.hide()
        self.snooze_warning_box.hide()

        self.movie.stop()
        self.hide()

        self.state = "idle"

        self.on_finish(next_delay_ms)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QApplication.quit()


class WaterReminderApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        if not os.path.exists(GIF_PATH):
            print("File target_transparent.gif belum ada.")
            print("Jalankan dulu: python make_transparent.py")
            sys.exit(1)

        self.window = WaterReminderWindow(
            gif_path=GIF_PATH,
            on_finish=self.schedule_next_reminder
        )

        self.next_timer = QTimer()
        self.next_timer.setSingleShot(True)
        self.next_timer.timeout.connect(self.window.play_reminder)

        self.setup_tray()

        if SHOW_ON_START:
            self.window.play_reminder()
        else:
            self.schedule_next_reminder(NORMAL_INTERVAL_MS)

    def schedule_next_reminder(self, delay_ms):
        self.next_timer.stop()
        self.next_timer.start(delay_ms)

        total_seconds = delay_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        next_time = datetime.now() + timedelta(milliseconds=delay_ms)

        print("=" * 50)
        print("💧 WATER DRINKING REMINDER")
        print(f"⏳ Countdown : {minutes:02d}:{seconds:02d}")
        print(f"🕒 Reminder  : {next_time.strftime('%H:%M:%S')}")
        print("=" * 50)

    def show_now(self):
        self.next_timer.stop()
        self.window.play_reminder()

    def setup_tray(self):
        self.tray = QSystemTrayIcon()

        icon = self.app.style().standardIcon(QStyle.SP_MessageBoxInformation)
        self.tray.setIcon(icon)
        self.tray.setToolTip("Water Reminder")

        menu = QMenu()

        show_now_action = QAction("Show Reminder Now")
        show_now_action.triggered.connect(self.show_now)

        hide_action = QAction("Hide Reminder")
        hide_action.triggered.connect(
            lambda: self.window.close_and_schedule(NORMAL_INTERVAL_MS)
        )

        quit_action = QAction("Quit")
        quit_action.triggered.connect(self.quit_app)

        menu.addAction(show_now_action)
        menu.addAction(hide_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def quit_app(self):
        self.next_timer.stop()
        self.window.movie.stop()
        self.window.hide()
        self.tray.hide()
        QApplication.quit()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = WaterReminderApp()
    app.run()
