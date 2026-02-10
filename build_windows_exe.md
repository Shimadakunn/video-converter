# Building the Windows .exe

## Prerequisites (on Windows)

1. **Install Python 3.11+** from https://python.org
   - During install, check "Add Python to PATH"

2. **Install FFmpeg** (must be included with the app):
   - Download from https://github.com/BtbN/FFmpeg-Builds/releases
   - Get `ffmpeg-master-latest-win64-gpl.zip`
   - Extract and copy `ffmpeg.exe` from the `bin` folder to this project folder

3. **Install PyInstaller**:
   ```
   pip install pyinstaller
   ```

## Build the .exe

Run this command in the project folder:

```
pyinstaller --onefile --windowed --name "DVD Converter" --add-binary "ffmpeg.exe;." dvd_converter_gui.py
```

The `.exe` will be created in the `dist` folder.

## What to give your mother

1. Copy `dist/DVD Converter.exe` to her computer
2. She double-clicks it, selects the DVD folder, clicks Convert
3. MP4 files appear in a "Converted_MP4" folder next to the originals
