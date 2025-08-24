# Media Tools

Utilities for renaming, organizing, and compressing media files.

Tools
- unified_media_renamer.py: Extract EXIF/MediaInfo and rename files.
- video_compress.py: Compress videos using ffmpeg.
- year_folder_script.py: Organize files into year-based folders.

Requirements
- Python 3.9+
- ffmpeg installed and on PATH (for video_compress.py)
- Python packages: see requirements.txt

Quick start
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

Examples
python3 unified_media_renamer.py --help
python3 video_compress.py --help
python3 year_folder_script.py --help
