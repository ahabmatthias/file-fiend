"""
Wrapper für unified_media_renamer.py (Projekt-Root)
Stellt collect_files und process_files für den UI-Tab bereit.
"""

import tqdm as _tqdm

import unified_media_renamer as _renamer_module
from unified_media_renamer import collect_files, process_files

# tqdm-Output unterdrücken: unified_media_renamer nutzt `from tqdm import tqdm`,
# daher die Referenz direkt im Modul überschreiben.
_orig_tqdm = _tqdm.tqdm
_silent = lambda *a, **kw: _orig_tqdm(*a, **{**kw, "disable": True})
_renamer_module.tqdm = _silent
_renamer_module.print = lambda *a, **kw: None  # type: ignore[attr-defined]  # print-Output unterdrücken

__all__ = ["collect_files", "process_files"]
