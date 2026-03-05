# FileFiend

A small desktop app to tame the mess on your hard drive — specifically photos, videos, and other media files that pile up over years of backups, camera imports, and "I'll sort this later" folders.

FileFiend started as a handful of Python scripts I wrote to clean up my own drives. Years of scattered backups had left me with duplicates everywhere, cryptic filenames like `DJI_1734.MOV`, and family videos shot in 4K that were eating terabytes for no good reason. I wrapped the scripts in a UI so I'd actually use them — and here we are.

It's not revolutionary. It won't be the fastest tool out there. But it's focused, it works offline, and it does exactly four things well:

- **Find Duplicates** — Scan folders for duplicate files using size pre-filtering and MD5 hashing. Review matches with thumbnail previews before deleting anything.
- **Batch Rename** — Rename media files to `YYYY-MM-DD_HHMMSS_original.ext` using EXIF or filesystem dates. Always previews changes before applying.
- **Organize by Year** — Sort files into `year/` folders based on date metadata. Optionally group by camera make/model from EXIF data.
- **Compress Video** — Batch HEVC encoding via ffmpeg with hardware acceleration. Shrink those 4K family videos without re-uploading anything anywhere.

The goal: you walk through your drive once, and when you're done, there are no duplicates, every file has a readable name, everything sits in the right folder, and your videos take up a fraction of the space. No cloud, no account, no internet connection required.

Built with [NiceGUI](https://nicegui.io) + [pywebview](https://pywebview.flowrl.com) for a native window on macOS and Windows.

## Download

Grab the latest build from [Releases](https://github.com/ahabmatthias/file-fiend/releases) — pre-built for macOS (Apple Silicon) and Windows.

**macOS Gatekeeper:** The app is not signed with an Apple Developer certificate. After downloading, remove the quarantine attribute before launching:

```bash
xattr -cr /path/to/FileFiend.app
```

## Run from Source

Requires Python 3.10+ and optionally [ffmpeg](https://ffmpeg.org/) on your PATH for video compression.

```bash
git clone https://github.com/ahabmatthias/file-fiend.git
cd file-fiend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

The app opens a native window. Pick a folder at the top, then use the tabs to find duplicates, rename, organize, or compress.

## Build from Source

**macOS (.app):**

```bash
bash build/macos/get_ffmpeg.sh   # download ffmpeg binaries
python build_app.py              # → dist/FileFiend.app
```

**Windows (.exe):**

```bash
python build/windows/get_ffmpeg.py      # download ffmpeg binaries
python build/windows/get_mediainfo.py   # download MediaInfo DLL
python build_app.py                     # → dist/FileFiend/FileFiend.exe
```

Releases are built automatically via GitHub Actions when a version tag is pushed.

## License

MIT
