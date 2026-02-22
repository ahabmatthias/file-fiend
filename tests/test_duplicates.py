"""
Tests für app/core/duplicates.py
"""

from pathlib import Path

from app.core.duplicates import find_duplicates


def test_no_duplicates(tmp_path):
    """Keine Duplikate wenn alle Dateien unterschiedlichen Inhalt haben."""
    (tmp_path / "a.jpg").write_bytes(b"content a")
    (tmp_path / "b.jpg").write_bytes(b"content b")
    (tmp_path / "c.jpg").write_bytes(b"content c")

    result = find_duplicates(str(tmp_path))

    assert result == {}


def test_finds_duplicates(tmp_dir_with_duplicates):
    """Zwei identische Dateien werden als Duplikat-Gruppe zurückgegeben."""
    result = find_duplicates(str(tmp_dir_with_duplicates))

    assert len(result) == 1
    group = list(result.values())[0]
    assert len(group) == 2
    names = {Path(p).name for p in group}
    assert names == {"file_a.jpg", "file_b.jpg"}


def test_unique_file_not_in_result(tmp_dir_with_duplicates):
    """Eine einzigartige Datei erscheint nicht in den Ergebnissen."""
    result = find_duplicates(str(tmp_dir_with_duplicates))

    all_paths = [p for group in result.values() for p in group]
    names = {Path(p).name for p in all_paths}
    assert "unique.jpg" not in names


def test_empty_directory(tmp_path):
    """Leeres Verzeichnis → keine Duplikate."""
    result = find_duplicates(str(tmp_path))

    assert result == {}


def test_single_file(tmp_path):
    """Nur eine Datei → keine Duplikate."""
    (tmp_path / "solo.jpg").write_bytes(b"only me")

    result = find_duplicates(str(tmp_path))

    assert result == {}


def test_empty_files_are_duplicates(tmp_path):
    """Zwei leere Dateien gelten als Duplikate (gleicher MD5-Hash)."""
    (tmp_path / "empty1.jpg").write_bytes(b"")
    (tmp_path / "empty2.jpg").write_bytes(b"")

    result = find_duplicates(str(tmp_path))

    assert len(result) == 1


def test_recursive_scan(tmp_path):
    """Duplikate in Unterordnern werden gefunden."""
    sub = tmp_path / "sub"
    sub.mkdir()
    content = b"same bytes"
    (tmp_path / "original.jpg").write_bytes(content)
    (sub / "copy.jpg").write_bytes(content)

    result = find_duplicates(str(tmp_path))

    assert len(result) == 1
