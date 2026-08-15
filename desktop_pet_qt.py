from __future__ import annotations

import sys
import time
from collections import deque
from pathlib import Path

from PIL import Image, ImageSequence
from PySide6.QtCore import QPoint, QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QIcon, QImage, QMouseEvent, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import QApplication, QMenu, QWidget


APP_NAME = "奶娃桌面宠物"
SIZES = (160, 220, 280, 360, 440)
def resource_path(name: str) -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / name


def pil_to_pixmap(image: Image.Image) -> QPixmap:
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimage = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimage)


def remove_edge_background(image: Image.Image) -> Image.Image:
    result = image.convert("RGBA")
    pixels = result.load()
    width, height = result.size
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def background(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        return a < 16 or (min(r, g, b) >= 155 and max(r, g, b) - min(r, g, b) <= 36)

    for x in range(width):
        queue.extend(((x, 0), (x, height - 1)))
    for y in range(height):
        queue.extend(((0, y), (width - 1, y)))

    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if visited[index]:
            continue
        visited[index] = 1
        if not background(x, y):
            continue
        pixels[x, y] = (0, 0, 0, 0)
        if x:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))
    return result


class DesktopPet(QWidget):
    def __init__(self) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle(APP_NAME)

        self.settings = QSettings("Codex", "NaiWaDesktopPet")
        self.pet_size = min(SIZES, key=lambda value: abs(value - int(self.settings.value("size", 280))))
        self.setFixedSize(QSize(self.pet_size, self.pet_size))
        self.paused = False
        self.drag_offset: QPoint | None = None
        self.idle_frames: list[QPixmap] = []
        self.idle_durations: list[int] = []
        self.idle_index = 0
        self.last_idle_frame = time.monotonic()
        self.load_assets()
        self.restore_position()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)

    def load_assets(self) -> None:
        with Image.open(resource_path("奶娃.gif")) as gif:
            default_duration = int(gif.info.get("duration", 60))
            for frame in ImageSequence.Iterator(gif):
                self.idle_frames.append(pil_to_pixmap(remove_edge_background(frame.convert("RGBA"))))
                self.idle_durations.append(max(20, int(frame.info.get("duration", default_duration))))
    def restore_position(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        default_x = screen.right() - self.pet_size - 24
        default_y = screen.bottom() - self.pet_size - 24
        x = int(self.settings.value("x", default_x))
        y = int(self.settings.value("y", default_y))
        self.move(max(screen.left(), min(x, screen.right() - self.pet_size)), max(screen.top(), min(y, screen.bottom() - self.pet_size)))

    def save_settings(self) -> None:
        self.settings.setValue("x", self.x())
        self.settings.setValue("y", self.y())
        self.settings.setValue("size", self.pet_size)

    def tick(self) -> None:
        if self.paused:
            return
        now = time.monotonic()
        if (now - self.last_idle_frame) * 1000 >= self.idle_durations[self.idle_index]:
            self.idle_index = (self.idle_index + 1) % len(self.idle_frames)
            self.last_idle_frame = now
            self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        pixmap = self.idle_frames[self.idle_index]
        side = self.pet_size
        rendered = pixmap.scaled(side, side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        painter.translate(self.pet_size / 2, self.pet_size / 2)
        painter.drawPixmap(-rendered.width() // 2, -rendered.height() // 2, rendered)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = None
            self.save_settings()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_pause()

    def wheelEvent(self, event: QWheelEvent) -> None:
        index = SIZES.index(self.pet_size)
        index = min(len(SIZES) - 1, index + 1) if event.angleDelta().y() > 0 else max(0, index - 1)
        self.change_size(SIZES[index])

    def change_size(self, size: int) -> None:
        if size == self.pet_size:
            return
        center_x = self.x() + self.pet_size // 2
        bottom = self.y() + self.pet_size
        self.pet_size = size
        self.setFixedSize(size, size)
        self.move(center_x - size // 2, bottom - size)
        self.save_settings()

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        pause = QAction("继续动画" if self.paused else "暂停动画", menu)
        pause.triggered.connect(self.toggle_pause)
        menu.addAction(pause)

        size_menu = menu.addMenu("调整大小")
        group = QActionGroup(size_menu)
        for value in SIZES:
            action = QAction(f"{value} 像素", size_menu, checkable=True, checked=value == self.pet_size)
            action.triggered.connect(lambda _checked=False, chosen=value: self.change_size(chosen))
            group.addAction(action)
            size_menu.addAction(action)
        menu.addSeparator()
        menu.addAction("退出", self.close)
        menu.exec(event.globalPos())

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def closeEvent(self, event) -> None:
        self.save_settings()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon_path = resource_path("icon_preview.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    pet = DesktopPet()
    pet.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
