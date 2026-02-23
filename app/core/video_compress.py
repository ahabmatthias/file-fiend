"""
Video-Komprimierung: Batch-HEVC-Encoding mit ffmpeg.

Stellt zwei öffentliche Funktionen bereit:
  preview_compression() – Dry-run, gibt strukturierte Liste zurück
  compress_files()      – Führt Komprimierung aus, unterstützt progress_cb
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTS = {".mp4", ".mov", ".m4v"}

_LOW_BITRATE_THRESHOLD_MBPS = 5.0


# ── Datenklassen ──────────────────────────────────────────────


@dataclass
class ProbeInfo:
    width: int | None
    height: int | None
    bitrate_bps: int | None


@dataclass
class Config:
    source: Path
    target: Path
    recursive: bool
    min_size_mb: float
    low_bitrate_threshold_mbps: float
    bitrate_4k: str
    bitrate_1440p: str
    bitrate_1080p: str
    bitrate_720p: str
    fallback_bitrate: str
    codec: str  # "auto", "hevc_videotoolbox", "libx265"
    copy_original_on_skip: bool
    overwrite: bool
    dry_run: bool
    audio_bitrate: str
    copy_audio: bool


# ── Hilfsfunktionen ───────────────────────────────────────────


def human_mb(bytes_size: float) -> float:
    return bytes_size / (1024 * 1024)


def detect_videotoolbox() -> bool:
    try:
        res = subprocess.run(
            ["ffmpeg", "-hide_banner", "-h", "encoder=hevc_videotoolbox"],
            capture_output=True,
            text=True,
        )
        return res.returncode == 0
    except Exception:
        return False


def collect_files(source: Path, recursive: bool) -> list[Path]:
    if recursive:
        files = [p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    else:
        files = [p for p in source.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    files.sort()
    return files


def ffprobe_json(path: Path) -> ProbeInfo:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,bit_rate",
        "-of",
        "json",
        str(path),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            return ProbeInfo(None, None, None)
        data = json.loads(res.stdout or "{}")
        streams = data.get("streams", [])
        if not streams:
            return ProbeInfo(None, None, None)
        s = streams[0]
        width = int(s.get("width")) if s.get("width") is not None else None
        height = int(s.get("height")) if s.get("height") is not None else None
        br = s.get("bit_rate")
        bitrate_bps = int(br) if br is not None else None
        return ProbeInfo(width, height, bitrate_bps)
    except Exception:
        return ProbeInfo(None, None, None)


def pick_target_bitrate(width: int | None, cfg: Config) -> str:
    if width is None:
        return cfg.fallback_bitrate
    if width >= 3840:
        return cfg.bitrate_4k
    if width >= 2560:
        return cfg.bitrate_1440p
    if width >= 1920:
        return cfg.bitrate_1080p
    return cfg.bitrate_720p


def should_skip_copy(
    file_path: Path,
    probe: ProbeInfo,
    min_size_mb: float,
    low_bitrate_threshold_mbps: float,
    target_bitrate_mbps: float,
) -> tuple[bool, str]:
    try:
        size_mb = human_mb(file_path.stat().st_size)
    except FileNotFoundError:
        return False, ""

    if size_mb < min_size_mb:
        return True, f"Überspringe kleine Datei ({size_mb:.1f} MB)"

    if probe.bitrate_bps and probe.width:
        current_mbps = probe.bitrate_bps / 1_000_000.0
        if current_mbps < low_bitrate_threshold_mbps and probe.width < 1920:
            return True, f"Bereits gut komprimiert ({current_mbps:.1f} Mbps)"
        if current_mbps <= target_bitrate_mbps * 1.2:
            return True, f"Bereits optimal komprimiert ({current_mbps:.1f} Mbps)"

    return False, ""


def build_ffmpeg_cmd(
    src: Path,
    dst: Path,
    video_codec: str,
    target_bitrate: str,
    audio_bitrate: str,
    copy_audio: bool,
) -> list[str]:
    cmd = [
        "ffmpeg",
        "-i",
        str(src),
        "-c:v",
        video_codec,
        "-b:v",
        target_bitrate,
        "-tag:v",
        "hvc1",
    ]
    if copy_audio:
        cmd += ["-c:a", "copy"]
    else:
        cmd += ["-c:a", "aac", "-b:a", audio_bitrate]
    cmd += ["-movflags", "+faststart", "-y", str(dst)]
    return cmd


# ── Konfiguration ─────────────────────────────────────────────


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


# ── Öffentliche API ───────────────────────────────────────────


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
                    "action": "skip_exists",
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
