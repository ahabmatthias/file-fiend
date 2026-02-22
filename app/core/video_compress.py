"""
Wrapper um video_compress.py (Root-Script) für UI-Integration.

Stellt zwei öffentliche Funktionen bereit:
  preview_compression() – Dry-run, gibt strukturierte Liste zurück
  compress_files()      – Führt Komprimierung aus, unterstützt progress_cb
"""

import shutil
import subprocess
from pathlib import Path

from video_compress import (
    Config,
    build_ffmpeg_cmd,
    collect_files,
    detect_videotoolbox,
    ffprobe_json,
    human_mb,
    pick_target_bitrate,
    should_skip_copy,
)

_LOW_BITRATE_THRESHOLD_MBPS = 5.0


def _make_config(
    source: Path,
    target: Path,
    recursive: bool,
    min_size_mb: float,
    codec: str,
    *,
    dry_run: bool,
) -> Config:
    return Config(
        source=source,
        target=target,
        recursive=recursive,
        min_size_mb=min_size_mb,
        low_bitrate_threshold_mbps=_LOW_BITRATE_THRESHOLD_MBPS,
        bitrate_4k="25M",
        bitrate_1440p="18M",
        bitrate_1080p="12M",
        bitrate_720p="8M",
        fallback_bitrate="15M",
        codec=codec,
        copy_original_on_skip=True,
        overwrite=False,
        dry_run=dry_run,
        audio_bitrate="128k",
        copy_audio=False,
    )


def preview_compression(
    source: str,
    target: str,
    *,
    recursive: bool = False,
    min_size_mb: float = 30.0,
    codec: str = "auto",
) -> list[dict]:
    """
    Dry-run: gibt je Datei ein Dict zurück – ohne tatsächlich zu encodieren.

    Jeder Eintrag:
        {name, size_mb, resolution, current_bitrate_mbps, target_bitrate, action}
    action: "compress" | "skip" | "skip_and_copy"
    """
    source_path = Path(source)
    target_path = Path(target)
    cfg = _make_config(source_path, target_path, recursive, min_size_mb, codec, dry_run=True)
    files = collect_files(source_path, recursive)
    result = []

    for src in files:
        dst_encoded = target_path / src.with_suffix(".mp4").name
        dst_copy = target_path / src.name

        try:
            size_mb = round(human_mb(src.stat().st_size), 1)
        except Exception:
            size_mb = 0.0

        # Bereits existierende Zieldatei → überspringen
        if not cfg.overwrite and (dst_encoded.exists() or dst_copy.exists()):
            result.append(
                {
                    "name": src.name,
                    "size_mb": size_mb,
                    "resolution": "–",
                    "current_bitrate_mbps": None,
                    "target_bitrate": "–",
                    "action": "skip",
                }
            )
            continue

        probe = ffprobe_json(src)
        target_bitrate = pick_target_bitrate(probe.width, cfg)
        target_bitrate_mbps = float(target_bitrate.rstrip("M"))

        do_skip, _ = should_skip_copy(
            src, probe, min_size_mb, _LOW_BITRATE_THRESHOLD_MBPS, target_bitrate_mbps
        )

        resolution = f"{probe.width}×{probe.height}" if probe.width and probe.height else "–"
        current_bitrate_mbps = (
            round(probe.bitrate_bps / 1_000_000, 1) if probe.bitrate_bps else None
        )

        action = (
            ("skip_and_copy" if cfg.copy_original_on_skip else "skip") if do_skip else "compress"
        )

        result.append(
            {
                "name": src.name,
                "size_mb": size_mb,
                "resolution": resolution,
                "current_bitrate_mbps": current_bitrate_mbps,
                "target_bitrate": target_bitrate,
                "action": action,
            }
        )

    return result


def compress_files(
    source: str,
    target: str,
    *,
    recursive: bool = False,
    min_size_mb: float = 30.0,
    codec: str = "auto",
    progress_cb=None,
) -> dict:
    """
    Führt Komprimierung aus.

    progress_cb(current, total, filename) wird vor jeder Datei aufgerufen.
    Gibt zurück: {compressed: int, skipped: int, failed: int, errors: list[str]}
    """
    source_path = Path(source)
    target_path = Path(target)

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        return {
            "compressed": 0,
            "skipped": 0,
            "failed": 0,
            "errors": ["ffmpeg/ffprobe nicht gefunden. Bitte im PATH verfügbar machen."],
        }

    target_path.mkdir(parents=True, exist_ok=True)

    use_vt = detect_videotoolbox() if codec == "auto" else codec == "hevc_videotoolbox"
    video_codec = "hevc_videotoolbox" if use_vt else "libx265"

    cfg = _make_config(source_path, target_path, recursive, min_size_mb, codec, dry_run=False)
    files = collect_files(source_path, recursive)
    total = len(files)
    compressed = skipped = failed = 0
    errors: list[str] = []

    for idx, src in enumerate(files, 1):
        if progress_cb:
            try:
                progress_cb(idx, total, src.name)
            except Exception:
                pass

        dst_encoded = target_path / src.with_suffix(".mp4").name
        dst_copy = target_path / src.name

        if not cfg.overwrite and (dst_encoded.exists() or dst_copy.exists()):
            skipped += 1
            continue

        probe = ffprobe_json(src)
        target_bitrate = pick_target_bitrate(probe.width, cfg)
        target_bitrate_mbps = float(target_bitrate.rstrip("M"))

        do_skip, _ = should_skip_copy(
            src, probe, min_size_mb, _LOW_BITRATE_THRESHOLD_MBPS, target_bitrate_mbps
        )

        if do_skip:
            if cfg.copy_original_on_skip:
                out = dst_copy
                if not cfg.overwrite and out.exists():
                    skipped += 1
                    continue
                try:
                    shutil.copy2(src, out)
                    skipped += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"{src.name}: {e}")
            else:
                skipped += 1
            continue

        cmd = build_ffmpeg_cmd(
            src, dst_encoded, video_codec, target_bitrate, cfg.audio_bitrate, cfg.copy_audio
        )
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0 and dst_encoded.exists():
                compressed += 1
            else:
                failed += 1
                stderr_lines = (proc.stderr or "").strip().splitlines()
                err_preview = " ".join(stderr_lines[-3:])[:200]
                errors.append(f"{src.name}: {err_preview}")
                try:
                    if dst_encoded.exists():
                        dst_encoded.unlink()
                except Exception:
                    pass
        except Exception as e:
            failed += 1
            errors.append(f"{src.name}: {e}")

    return {"compressed": compressed, "skipped": skipped, "failed": failed, "errors": errors}
