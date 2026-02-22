"""
Shared fixtures für alle Tests.
"""

import pytest


@pytest.fixture
def tmp_media_dir(tmp_path):
    """Temporäres Verzeichnis mit Beispiel-Mediendateien (mit Jahreszahl im Namen)."""
    for name in [
        "2023-01-15_120000_foto1.jpg",
        "2023-06-20_083000_foto2.jpg",
        "2024-03-10_150000_video1.mp4",
        "2024-11-05_091500_foto3.png",
    ]:
        (tmp_path / name).write_bytes(b"fake media content " + name.encode())
    return tmp_path


@pytest.fixture
def tmp_dir_with_duplicates(tmp_path):
    """Temporäres Verzeichnis mit zwei identischen Dateien."""
    content = b"identical content"
    (tmp_path / "file_a.jpg").write_bytes(content)
    (tmp_path / "file_b.jpg").write_bytes(content)
    (tmp_path / "unique.jpg").write_bytes(b"different content")
    return tmp_path


@pytest.fixture
def tmp_dir_no_year(tmp_path):
    """Temporäres Verzeichnis mit Dateien ohne erkennbares Jahr."""
    (tmp_path / "IMG_1234.jpg").write_bytes(b"no year in name")
    (tmp_path / "DSC_5678.jpg").write_bytes(b"no year in name either")
    return tmp_path


@pytest.fixture
def tmp_dir_conflict(tmp_path):
    """Verzeichnis mit zwei Dateien gleichem Namen in verschiedenen Unterordnern."""
    sub1 = tmp_path / "sub1"
    sub2 = tmp_path / "sub2"
    sub1.mkdir()
    sub2.mkdir()
    (sub1 / "2023-05-01_120000_foto.jpg").write_bytes(b"content a")
    (sub2 / "2023-05-01_120000_foto.jpg").write_bytes(b"content b")
    return tmp_path
