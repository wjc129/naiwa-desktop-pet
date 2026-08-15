from pathlib import Path

import PyInstaller.__main__


root = Path(__file__).resolve().parent
PyInstaller.__main__.run(
    [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
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
