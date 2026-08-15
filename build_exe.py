from pathlib import Path
import runpy

import PyInstaller.__main__


root = Path(__file__).resolve().parent
runpy.run_path(str(root / "make_icon.py"), run_name="__main__")
PyInstaller.__main__.run(
    [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--icon",
        str(root / "奶娃.ico"),
        "--name",
        "奶娃桌面宠物",
        "--add-data",
        f"{root / '奶娃.gif'};.",
        "--distpath",
        str(root / "dist"),
        "--workpath",
        str(root / "build"),
        "--specpath",
        str(root / "build"),
        str(root / "desktop_pet.pyw"),
    ]
)
