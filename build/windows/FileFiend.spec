# -*- mode: python ; coding: utf-8 -*-
"""
FileFiend – PyInstaller Spec (Windows)
Build mit: python build_app.py
"""

import importlib.util
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ── Pfade ermitteln ──────────────────────────────────────────
ROOT = Path(SPECPATH).parent.parent  # build/windows/ → Projekt-Root

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
if (vendor_dir / "ffmpeg.exe").exists():
    binaries.append((str(vendor_dir / "ffmpeg.exe"), "vendor"))
if (vendor_dir / "ffprobe.exe").exists():
    binaries.append((str(vendor_dir / "ffprobe.exe"), "vendor"))
if (vendor_dir / "MediaInfo.dll").exists():
    binaries.append((str(vendor_dir / "MediaInfo.dll"), "vendor"))

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
    # pywebview (kein PyObjC auf Windows nötig)
    "webview",
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
icon_path = ROOT / "assets" / "FileFiend.ico"
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FileFiend",
)
