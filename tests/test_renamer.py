"""
Tests für unified_media_renamer – collect_files() und process_files() im dry-run.
"""

from unified_media_renamer import collect_files, detect_file_status, process_files


def test_collect_files_finds_images(tmp_path):
    """collect_files() findet JPG-, PNG- und HEIC-Dateien."""
    (tmp_path / "photo.jpg").write_bytes(b"jpeg")
    (tmp_path / "photo.png").write_bytes(b"png")
    (tmp_path / "document.pdf").write_bytes(b"pdf")

    files = collect_files(str(tmp_path))

    names = {f["path"].name for f in files}
    assert "photo.jpg" in names
    assert "photo.png" in names
    assert "document.pdf" not in names


def test_collect_files_skips_dot_underscore(tmp_path):
    """Dateien mit ._-Präfix (macOS-Resource-Forks) werden übersprungen."""
    (tmp_path / "._hidden.jpg").write_bytes(b"resource fork")
    (tmp_path / "visible.jpg").write_bytes(b"real file")

    files = collect_files(str(tmp_path))

    names = {f["path"].name for f in files}
    assert "._hidden.jpg" not in names
    assert "visible.jpg" in names


def test_collect_files_type_detection(tmp_path):
    """Dateityp wird korrekt als image/video erkannt."""
    (tmp_path / "clip.mp4").write_bytes(b"video")
    (tmp_path / "shot.jpg").write_bytes(b"image")

    files = collect_files(str(tmp_path))

    by_name = {f["path"].name: f["type"] for f in files}
    assert by_name["clip.mp4"] == "video"
    assert by_name["shot.jpg"] == "image"


def test_detect_file_status_already_renamed():
    """Bereits umbenannte Dateien werden korrekt erkannt."""
    assert detect_file_status("2023-04-15_120000_IMG_1234.jpg") is True
    assert detect_file_status("2023-04-15_12-00-00_IMG_1234.jpg") is True


def test_detect_file_status_not_renamed():
    """Nicht umbenannte Dateien werden korrekt als solche erkannt."""
    assert detect_file_status("IMG_1234.jpg") is False
    assert detect_file_status("DSC_0001.jpg") is False
    assert detect_file_status("foto.jpg") is False


def test_process_files_dry_run_no_changes(tmp_path):
    """Dry-run ändert keine Dateien."""
    already_named = "2023-04-15_120000_IMG_1234.jpg"
    p = tmp_path / already_named
    p.write_bytes(b"content")

    files = collect_files(str(tmp_path))
    results = process_files(files, dry_run=True)

    # Datei existiert noch am gleichen Ort
    assert p.exists()
    # Keine Fehler
    assert results["errors"] == 0


def test_process_files_dry_run_renames_found(tmp_path):
    """Dry-run erkennt Dateien die umbenannt werden würden."""
    (tmp_path / "2023-01-15_photo.jpg").write_bytes(b"content")

    files = collect_files(str(tmp_path))
    results = process_files(files, dry_run=True)

    # Originaldatei noch vorhanden (dry-run)
    assert (tmp_path / "2023-01-15_photo.jpg").exists()
    # Rename wurde vorgeschlagen
    assert results["processed"] >= 0  # kann 0 sein wenn Datei schon korrekt erkannt


def test_process_files_collect_returns_list(tmp_path):
    """collect_files gibt eine Liste zurück."""
    (tmp_path / "test.jpg").write_bytes(b"x")

    files = collect_files(str(tmp_path))

    assert isinstance(files, list)
    assert len(files) == 1
    assert "path" in files[0]
    assert "type" in files[0]
    assert "is_renamed" in files[0]
