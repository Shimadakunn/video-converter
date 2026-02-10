"""
DVD to MP4 Converter - Simple GUI for Windows

A user-friendly application to convert DVD VIDEO_TS folders to MP4 files.
"""

import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


def get_ffmpeg_path() -> str:
    """Get path to ffmpeg executable, handling PyInstaller bundling."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle - ffmpeg is in the temp extraction folder
        bundle_dir = Path(sys._MEIPASS)
        ffmpeg_path = bundle_dir / "ffmpeg.exe"
        if ffmpeg_path.exists():
            return str(ffmpeg_path)
    # Fallback to system PATH
    return "ffmpeg"


class DVDConverterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DVD to MP4 Converter")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 500) // 2
        y = (self.root.winfo_screenheight() - 350) // 2
        self.root.geometry(f"500x350+{x}+{y}")

        self.selected_folder: Path | None = None
        self.is_converting = False

        self._create_widgets()

    def _create_widgets(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="🎬 DVD to MP4 Converter",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Instructions
        instructions = ttk.Label(
            main_frame,
            text="Convert your DVD videos to MP4 format.\n"
                 "Select the folder containing your DVD files (.VOB files).",
            justify=tk.CENTER,
            font=("Segoe UI", 10)
        )
        instructions.pack(pady=(0, 20))

        # Folder selection frame
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 15))

        self.folder_label = ttk.Label(
            folder_frame,
            text="No folder selected",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.browse_button = ttk.Button(
            folder_frame,
            text="📁 Select Folder",
            command=self._browse_folder
        )
        self.browse_button.pack(side=tk.RIGHT, padx=(10, 0))

        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode="indeterminate",
            length=460
        )
        self.progress.pack(pady=(0, 10))

        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9),
            foreground="blue"
        )
        self.status_label.pack(pady=(0, 15))

        # Convert button
        self.convert_button = ttk.Button(
            main_frame,
            text="▶ Convert to MP4",
            command=self._start_conversion,
            state=tk.DISABLED
        )
        self.convert_button.pack(pady=(0, 10))

        # Open output folder button (hidden initially)
        self.open_folder_button = ttk.Button(
            main_frame,
            text="📂 Open Output Folder",
            command=self._open_output_folder
        )
        self.output_folder: Path | None = None

    def _browse_folder(self):
        folder = filedialog.askdirectory(
            title="Select DVD Folder (containing .VOB files)"
        )
        if folder:
            self.selected_folder = Path(folder)
            # Truncate long paths for display
            display_path = str(self.selected_folder)
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]
            self.folder_label.config(text=display_path, foreground="black")
            self.convert_button.config(state=tk.NORMAL)
            self.status_label.config(text="")
            self.open_folder_button.pack_forget()

    def _start_conversion(self):
        if self.is_converting or not self.selected_folder:
            return

        # Check for VOB files
        vob_files = self._get_vob_files(self.selected_folder)
        if not vob_files:
            messagebox.showerror(
                "No Videos Found",
                "No DVD video files (.VOB) found in the selected folder.\n\n"
                "Make sure you selected the correct folder."
            )
            return

        # Check for FFmpeg
        if not self._check_ffmpeg():
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg is required but not installed.\n\n"
                "Please install FFmpeg from: https://ffmpeg.org/download.html"
            )
            return

        self.is_converting = True
        self.convert_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.DISABLED)
        self.progress.start(10)
        self.open_folder_button.pack_forget()

        # Run conversion in background thread
        thread = threading.Thread(target=self._convert, args=(vob_files,))
        thread.daemon = True
        thread.start()

    def _get_vob_files(self, folder: Path) -> list[Path]:
        """Get VOB files larger than 1MB (actual video content)."""
        vob_files = sorted(folder.glob("*.VOB"))
        return [f for f in vob_files if f.stat().st_size > 1_000_000]

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            subprocess.run(
                [get_ffmpeg_path(), "-version"],
                capture_output=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _convert(self, vob_files: list[Path]):
        """Run conversion in background thread."""
        output_dir = self.selected_folder.parent / "Converted_MP4"
        output_dir.mkdir(exist_ok=True)
        self.output_folder = output_dir

        success_count = 0
        total = len(vob_files)

        for i, vob in enumerate(vob_files, 1):
            self._update_status(f"Converting {i}/{total}: {vob.name}...")

            output_path = output_dir / (vob.stem + ".mp4")

            cmd = [
                get_ffmpeg_path(),
                "-i", str(vob),
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "20",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "-y",
                str(output_path)
            ]

            try:
                # Hide console window on Windows
                creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                subprocess.run(cmd, check=True, capture_output=True, creationflags=creation_flags)
                success_count += 1
            except subprocess.CalledProcessError:
                pass

        # Update UI on main thread
        self.root.after(0, lambda: self._conversion_complete(success_count, total))

    def _update_status(self, text: str):
        """Update status label from any thread."""
        self.root.after(0, lambda: self.status_label.config(text=text))

    def _conversion_complete(self, success: int, total: int):
        """Called when conversion finishes."""
        self.is_converting = False
        self.progress.stop()
        self.convert_button.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.NORMAL)

        if success == total:
            self.status_label.config(
                text=f"✓ Successfully converted {success} video(s)!",
                foreground="green"
            )
            self.open_folder_button.pack(pady=(0, 10))
        elif success > 0:
            self.status_label.config(
                text=f"⚠ Converted {success}/{total} videos (some failed)",
                foreground="orange"
            )
            self.open_folder_button.pack(pady=(0, 10))
        else:
            self.status_label.config(
                text="✗ Conversion failed",
                foreground="red"
            )
            messagebox.showerror(
                "Conversion Failed",
                "Could not convert the videos. Please check that the files are valid DVD videos."
            )

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        if self.output_folder and self.output_folder.exists():
            if sys.platform == "win32":
                subprocess.run(["explorer", str(self.output_folder)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.output_folder)])
            else:
                subprocess.run(["xdg-open", str(self.output_folder)])


def main():
    root = tk.Tk()
    app = DVDConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
