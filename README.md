# FileFiend

A desktop app for managing photos and videos. Find duplicates, batch-rename files by date, organize into year folders, and compress videos — all from a single interface.

Built with [NiceGUI](https://nicegui.io) + [pywebview](https://pywebview.flowrl.com) for a native window on macOS and Windows.

## Features

- **Duplicate Finder** — Scans a folder for duplicate files using size pre-filtering and MD5 hashing. Select and delete duplicates with thumbnail previews.
- **Batch Renamer** — Renames media files to `YYYY-MM-DD_HHMMSS_original.ext` using EXIF or filesystem dates. Dry-run preview before applying.
- **Year Organizer** — Sorts files into `year/` folders based on date metadata. Optional camera sub-folders using EXIF make/model.
- **Video Compressor** — Batch HEVC encoding via ffmpeg with hardware acceleration support. Shows file sizes, bitrate, and progress.

## Requirements

- Python 3.10+ (3.13 recommended)
- [ffmpeg + ffprobe](https://ffmpeg.org/) on your PATH (required for video compression)
- macOS or Windows

## Setup

```bash
git clone https://github.com/ahabmatthias/file-fiend.git
cd file-fiend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m app.main
```

The app opens a native window. Pick a folder at the top, then use the tabs to find duplicates, rename, organize, or compress.

## Build

**macOS (.app):**

```bash
python build_app.py
# → dist/FileFiend.app
```

Requires vendor binaries — run `bash build/macos/get_ffmpeg.sh` first if needed.

**Windows (.exe):**

Built via GitHub Actions. Push to a branch and trigger the `build-windows.yml` workflow.

## License

MIT
