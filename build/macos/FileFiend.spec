# -*- mode: python ; coding: utf-8 -*-
"""
FileFiend – PyInstaller Spec
Build mit: python build_app.py
"""

import importlib.util
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ── Pfade ermitteln ──────────────────────────────────────────
ROOT = Path(SPECPATH).parent.parent  # build/macos/ → Projekt-Root

nicegui_path = Path(importlib.util.find_spec("nicegui").submodule_search_locations[0])
pymediainfo_path = Path(importlib.util.find_spec("pymediainfo").submodule_search_locations[0])

# ── collect_all für Packages mit dynamischen Imports ─────────
_socketio_d, _socketio_b, _socketio_h = collect_all("socketio")
_engineio_d, _engineio_b, _engineio_h = collect_all("engineio")

# ── Daten & Binaries ────────────────────────────────────────
datas = [
    (str(nicegui_path), "nicegui"),
    (str(pymediainfo_path), "pymediainfo"),
    *_socketio_d,
    *_engineio_d,
]

binaries = [*_socketio_b, *_engineio_b]
vendor_dir = ROOT / "vendor"
if (vendor_dir / "ffmpeg").exists():
    binaries.append((str(vendor_dir / "ffmpeg"), "vendor"))
if (vendor_dir / "ffprobe").exists():
    binaries.append((str(vendor_dir / "ffprobe"), "vendor"))

# ── Hidden Imports ───────────────────────────────────────────
hiddenimports = [
    # NiceGUI Webstack
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "starlette",
    "starlette.routing",
    "starlette.responses",
    # Socket.IO / Engine.IO
    "engineio",
    "engineio.async_drivers",
    "engineio.async_drivers.aiohttp",
    "socketio",
    "socketio.async_server",
    # pywebview + pyobjc
    "webview",
    "objc",
    "Foundation",
    "AppKit",
    "WebKit",
    "PyObjCTools",
    # App-eigene Packages
    "PIL",
    "PIL.Image",
    "PIL.ExifTags",
    "pillow_heif",
    "pymediainfo",
    "tqdm",
    # NiceGUI internals
    "nicegui",
    "nicegui.native",
    "nicegui.native.native_mode",
]

# ── Icon ─────────────────────────────────────────────────────
icon_path = ROOT / "assets" / "FileFiend.icns"
icon_file = str(icon_path) if icon_path.exists() else None

# ── Analysis ─────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + _socketio_h + _engineio_h,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "numpy.testing"],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FileFiend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_file,
    target_arch="arm64",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FileFiend",
)

app = BUNDLE(
    coll,
    name="FileFiend.app",
    icon=icon_file,
    bundle_identifier="com.filefiend.app",
    info_plist={
        "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
        "CFBundleShortVersionString": "1.0.0",
        "NSDesktopFolderUsageDescription": "FileFiend benötigt Zugriff auf Ordner zum Verarbeiten von Medien-Dateien.",
        "NSDocumentsFolderUsageDescription": "FileFiend benötigt Zugriff auf Ordner zum Verarbeiten von Medien-Dateien.",
        "NSDownloadsFolderUsageDescription": "FileFiend benötigt Zugriff auf Ordner zum Verarbeiten von Medien-Dateien.",
    },
)
