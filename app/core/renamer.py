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

__all__ = ["collect_files", "process_files"]
