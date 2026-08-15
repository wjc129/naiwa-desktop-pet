from pathlib import Path
import runpy

from PIL import Image


root = Path(__file__).resolve().parent
namespace = runpy.run_path(str(root / "desktop_pet.pyw"), run_name="pet_icon_module")
remove_background = namespace["DesktopPet"].remove_edge_background

with Image.open(root / "奶娃.gif") as gif:
    frame = remove_background(gif.convert("RGBA"))

# 放大脸部与思考手势，在 16x16/32x32 的小图标上也能辨认。
portrait = frame.crop((42, 8, 278, 244))
portrait = portrait.resize((256, 256), Image.Resampling.LANCZOS)

# 清理缩放后极浅的半透明边缘。
alpha = portrait.getchannel("A").point(lambda value: 0 if value < 18 else value)
portrait.putalpha(alpha)

portrait.save(root / "icon_preview.png")
portrait.resize((1024, 1024), Image.Resampling.LANCZOS).save(root / "奶娃.icns", format="ICNS")
portrait.save(
    root / "奶娃.ico",
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(root / "奶娃.ico")
