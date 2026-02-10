#!/usr/bin/env python3
"""
DVD VOB to MP4 Converter

Converts DVD VIDEO_TS structure (.VOB files) to modern MP4 format
using H.264 video codec and AAC audio for maximum compatibility.
"""

import subprocess
import sys
from pathlib import Path


def get_vob_files(input_dir: Path) -> list[Path]:
    """
    Get VOB files that contain actual video content.
    Filters out small menu/navigation VOBs (< 1MB).
    """
    vob_files = sorted(input_dir.glob("*.VOB"))
    return [f for f in vob_files if f.stat().st_size > 1_000_000]


def convert_vob_to_mp4(vob_path: Path, output_dir: Path) -> bool:
    """Convert a single VOB file to MP4 using FFmpeg."""
    output_name = vob_path.stem + ".mp4"
    output_path = output_dir / output_name

    print(f"\n{'='*60}")
    print(f"Converting: {vob_path.name}")
    print(f"Output:     {output_path.name}")
    print(f"{'='*60}")

    cmd = [
        "ffmpeg",
        "-i", str(vob_path),
        "-c:v", "libx264",      # H.264 video codec (universal compatibility)
        "-preset", "medium",    # Balance between speed and compression
        "-crf", "20",           # Quality (18-23 is visually lossless range)
        "-c:a", "aac",          # AAC audio codec
        "-b:a", "192k",         # Audio bitrate
        "-movflags", "+faststart",  # Enable streaming playback
        "-y",                   # Overwrite output without asking
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"Done: {output_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting {vob_path.name}: {e}", file=sys.stderr)
        return False


def main():
    input_dir = Path(__file__).parent / "videos"
    output_dir = Path(__file__).parent / "converted"

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(exist_ok=True)

    vob_files = get_vob_files(input_dir)

    if not vob_files:
        print("No VOB files found to convert.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(vob_files)} video file(s) to convert:")
    for vob in vob_files:
        size_mb = vob.stat().st_size / (1024 * 1024)
        print(f"  - {vob.name} ({size_mb:.1f} MB)")

    success_count = 0
    for vob in vob_files:
        if convert_vob_to_mp4(vob, output_dir):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"Conversion complete: {success_count}/{len(vob_files)} files converted")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
