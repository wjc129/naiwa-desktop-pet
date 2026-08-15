import os
import platform
import runpy
from pathlib import Path

import PyInstaller.__main__


root = Path(__file__).resolve().parent
runpy.run_path(str(root / "make_icon.py"), run_name="__main__")
system = platform.system()
icon = root / ("奶娃.ico" if system == "Windows" else "奶娃.icns" if system == "Darwin" else "icon_preview.png")
separator = os.pathsep

arguments = [
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name",
    "NaiWaDesktopPet",
    "--icon",
    str(icon),
    "--add-data",
    f"{root / '奶娃.gif'}{separator}.",
    "--add-data",
    f"{root / 'icon_preview.png'}{separator}.",
    "--distpath",
    str(root / "dist"),
    "--workpath",
    str(root / "build" / system.lower()),
    "--specpath",
    str(root / "build"),
    str(root / "desktop_pet_qt.py"),
]
if system == "Darwin":
    arguments.extend(["--osx-bundle-identifier", "com.codex.naiwa-desktop-pet"])
PyInstaller.__main__.run(arguments)
