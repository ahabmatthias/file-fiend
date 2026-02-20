"""
Wrapper für unified_media_renamer.py (Projekt-Root)
Stellt collect_files und process_files für den UI-Tab bereit.
"""

import sys
from pathlib import Path

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from unified_media_renamer import collect_files, process_files  # noqa: E402
import unified_media_renamer as _renamer_module

# tqdm-Output unterdrücken: unified_media_renamer nutzt `from tqdm import tqdm`,
# daher die Referenz direkt im Modul überschreiben.
import tqdm as _tqdm
_orig_tqdm = _tqdm.tqdm
_silent = lambda *a, **kw: _orig_tqdm(*a, **{**kw, "disable": True})
_renamer_module.tqdm = _silent
_renamer_module.print = lambda *a, **kw: None  # print-Output im Terminal unterdrücken

__all__ = ["collect_files", "process_files"]
