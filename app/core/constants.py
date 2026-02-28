"""
Zentrale Dateiendungen für alle Module.
"""

IMAGE_EXTS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp"})
VIDEO_EXTS: frozenset[str] = frozenset({".mp4", ".mov", ".avi", ".mkv", ".m4v"})
AUDIO_EXTS: frozenset[str] = frozenset({".aac", ".wav", ".mp3", ".m4a"})
ALL_MEDIA_EXTS: frozenset[str] = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS
