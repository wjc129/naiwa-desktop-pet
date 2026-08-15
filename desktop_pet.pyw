from __future__ import annotations

import ctypes
import json
import os
import sys
import tkinter as tk
from collections import deque
from pathlib import Path

from PIL import Image, ImageSequence, ImageTk


APP_NAME = "奶娃桌面宠物"
CHROMA = (255, 0, 255)
CHROMA_HEX = "#ff00ff"
SIZES = (160, 220, 280, 360, 440)


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def settings_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "NaiWaDesktopPet"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


class DesktopPet:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=CHROMA_HEX)
        try:
            self.root.wm_attributes("-transparentcolor", CHROMA_HEX)
        except tk.TclError:
            pass

        self.settings = self.load_settings()
        self.size = min(SIZES, key=lambda value: abs(value - self.settings.get("size", 280)))
        self.paused = False
        self.frame_index = 0
        self.drag_origin: tuple[int, int, int, int] | None = None
        self.frames: list[ImageTk.PhotoImage] = []
        self.durations: list[int] = []
        self.raw_frames: list[Image.Image] = []

        self.label = tk.Label(self.root, bd=0, highlightthickness=0, bg=CHROMA_HEX)
        self.label.pack()
        self.label.bind("<ButtonPress-1>", self.begin_drag)
        self.label.bind("<B1-Motion>", self.drag)
        self.label.bind("<ButtonRelease-1>", self.end_drag)
        self.label.bind("<Button-3>", self.show_menu)
        self.label.bind("<Double-Button-1>", lambda _event: self.toggle_pause())
        self.label.bind("<MouseWheel>", self.mousewheel_resize)

        self.menu = tk.Menu(self.root, tearoff=False, font=("Microsoft YaHei UI", 10))
        self.menu.add_command(label="暂停动画", command=self.toggle_pause)
        size_menu = tk.Menu(self.menu, tearoff=False, font=("Microsoft YaHei UI", 10))
        for value in SIZES:
            size_menu.add_command(label=f"{value} 像素", command=lambda chosen=value: self.set_size(chosen))
        self.menu.add_cascade(label="调整大小", menu=size_menu)
        self.menu.add_command(label="回到右下角", command=self.move_to_corner)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.close)

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.load_gif()
        self.rebuild_frames()
        self.place_initially()
        self.root.after(20, self.hide_from_taskbar)
        self.root.after(self.durations[0], self.animate)

    def load_settings(self) -> dict:
        try:
            return json.loads(settings_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_settings(self) -> None:
        data = {"x": self.root.winfo_x(), "y": self.root.winfo_y(), "size": self.size}
        try:
            settings_path().write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def load_gif(self) -> None:
        path = resource_path("奶娃.gif")
        with Image.open(path) as gif:
            for frame in ImageSequence.Iterator(gif):
                rgba = frame.convert("RGBA")
                self.raw_frames.append(self.remove_edge_background(rgba))
                self.durations.append(max(20, int(frame.info.get("duration", gif.info.get("duration", 60)))))

    @staticmethod
    def remove_edge_background(image: Image.Image) -> Image.Image:
        """只删除与图片边缘连通的近白背景，保留角色内部的浅色区域。"""
        result = image.copy()
        pixels = result.load()
        width, height = result.size
        visited = bytearray(width * height)
        queue: deque[tuple[int, int]] = deque()

        def background(x: int, y: int) -> bool:
            r, g, b, a = pixels[x, y]
            # 原 GIF 的底部含有比白色更深的中性灰阴影。
            # 因为搜索只从画面边缘向内扩展，放宽阈值不会删掉
            # 被黄色身体包围的腹部高光和内部阴影。
            return a < 16 or (min(r, g, b) >= 155 and max(r, g, b) - min(r, g, b) <= 36)

        for x in range(width):
            queue.append((x, 0))
            queue.append((x, height - 1))
        for y in range(height):
            queue.append((0, y))
            queue.append((width - 1, y))

        while queue:
            x, y = queue.popleft()
            index = y * width + x
            if visited[index]:
                continue
            visited[index] = 1
            if not background(x, y):
                continue
            pixels[x, y] = (0, 0, 0, 0)
            if x > 0:
                queue.append((x - 1, y))
            if x + 1 < width:
                queue.append((x + 1, y))
            if y > 0:
                queue.append((x, y - 1))
            if y + 1 < height:
                queue.append((x, y + 1))
        return result

    def rebuild_frames(self) -> None:
        self.frames.clear()
        for raw in self.raw_frames:
            resized = raw.resize((self.size, self.size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", resized.size, CHROMA)
            alpha = resized.getchannel("A").point(lambda value: 255 if value >= 96 else 0)
            canvas.paste(resized.convert("RGB"), mask=alpha)
            self.frames.append(ImageTk.PhotoImage(canvas))
        self.frame_index %= len(self.frames)
        self.label.configure(image=self.frames[self.frame_index], width=self.size, height=self.size)
        self.root.geometry(f"{self.size}x{self.size}+{self.root.winfo_x()}+{self.root.winfo_y()}")

    def animate(self) -> None:
        if not self.paused:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.label.configure(image=self.frames[self.frame_index])
        self.root.after(self.durations[self.frame_index], self.animate)

    def begin_drag(self, event: tk.Event) -> None:
        self.drag_origin = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y())

    def drag(self, event: tk.Event) -> None:
        if self.drag_origin is None:
            return
        start_x, start_y, window_x, window_y = self.drag_origin
        self.root.geometry(f"+{window_x + event.x_root - start_x}+{window_y + event.y_root - start_y}")

    def end_drag(self, _event: tk.Event) -> None:
        self.drag_origin = None
        self.keep_on_screen()
        self.save_settings()

    def keep_on_screen(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = min(max(self.root.winfo_x(), 0), max(0, screen_w - self.size))
        y = min(max(self.root.winfo_y(), 0), max(0, screen_h - self.size - 40))
        self.root.geometry(f"+{x}+{y}")

    def place_initially(self) -> None:
        x = self.settings.get("x")
        y = self.settings.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            self.move_to_corner()
        else:
            self.root.geometry(f"{self.size}x{self.size}+{x}+{y}")
            self.root.update_idletasks()
            self.keep_on_screen()

    def move_to_corner(self) -> None:
        x = self.root.winfo_screenwidth() - self.size - 28
        y = self.root.winfo_screenheight() - self.size - 76
        self.root.geometry(f"{self.size}x{self.size}+{max(0, x)}+{max(0, y)}")
        self.save_settings()

    def show_menu(self, event: tk.Event) -> None:
        self.menu.entryconfigure(0, label="继续动画" if self.paused else "暂停动画")
        self.menu.tk_popup(event.x_root, event.y_root)

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def mousewheel_resize(self, event: tk.Event) -> None:
        index = SIZES.index(self.size)
        index = min(len(SIZES) - 1, index + 1) if event.delta > 0 else max(0, index - 1)
        self.set_size(SIZES[index])

    def set_size(self, size: int) -> None:
        if size == self.size:
            return
        center_x = self.root.winfo_x() + self.size // 2
        bottom = self.root.winfo_y() + self.size
        self.size = size
        self.rebuild_frames()
        self.root.geometry(f"{size}x{size}+{center_x - size // 2}+{bottom - size}")
        self.keep_on_screen()
        self.save_settings()

    def hide_from_taskbar(self) -> None:
        if sys.platform != "win32":
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, (style & ~0x00040000) | 0x00000080)
        except Exception:
            pass

    def close(self) -> None:
        self.save_settings()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DesktopPet().run()
