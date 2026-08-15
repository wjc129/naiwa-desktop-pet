# 奶娃桌面宠物

一个为 Windows 制作的轻量级 GIF 桌面宠物。支持透明背景、窗口置顶、拖动、缩放和动画暂停。

## 功能

- 透明无边框窗口，始终保持在桌面顶层
- 自动播放 97 帧奶娃 GIF 动画
- 左键拖动，滚轮缩放
- 双击暂停或继续，右键打开功能菜单
- 自动记住上次的位置和大小
- 通过边缘连通区域检测去除 GIF 白色及灰色背景

## 使用

从 [Releases](../../releases) 下载 `NaiWaDesktopPet.exe`，双击即可运行。

也可以通过 Python 运行：

```bat
conda activate beijing
pip install -r requirements.txt
pythonw desktop_pet.pyw
```

## 构建 EXE

```bat
conda activate beijing
python build_exe.py
```

构建结果位于 `dist\奶娃桌面宠物.exe`。

## 许可证

项目代码使用 [MIT License](LICENSE) 开源。请确保在再分发时拥有动画素材 `奶娃.gif` 的相应使用权。
