#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


SUPPORTED_EXTS = {".mp4", ".mov", ".m4v"}


@dataclass
class ProbeInfo:
    width: Optional[int]
    height: Optional[int]
    bitrate_bps: Optional[int]


def which_or_hint(name: str) -> bool:
    return shutil.which(name) is not None


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


def collect_files(source: Path, recursive: bool) -> List[Path]:
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


def pick_target_bitrate(width: Optional[int], cfg: "Config") -> str:
    if width is None:
        return cfg.fallback_bitrate
    if width >= 3840:
        return cfg.bitrate_4k
    if width >= 2560:
        return cfg.bitrate_1440p
    if width >= 1920:
        return cfg.bitrate_1080p
    return cfg.bitrate_720p


def human_mb(bytes_size: float) -> float:
    return bytes_size / (1024 * 1024)


def should_skip_copy(
    file_path: Path,
    probe: ProbeInfo,
    min_size_mb: float,
    low_bitrate_threshold_mbps: float,
    target_bitrate_mbps: float,
) -> Tuple[bool, str]:
    try:
        size_mb = human_mb(file_path.stat().st_size)
    except FileNotFoundError:
        return False, ""

    if size_mb < min_size_mb:
        return True, f"⏩ Überspringe kleine Datei ({size_mb:.1f} MB)"

    # If we have a bitrate, apply heuristics
    if probe.bitrate_bps and probe.width:
        current_mbps = probe.bitrate_bps / 1_000_000.0
        if current_mbps < low_bitrate_threshold_mbps and probe.width < 1920:
            return True, f"⏩ Bereits gut komprimiert ({current_mbps:.1f} Mbps)"
        if current_mbps <= target_bitrate_mbps * 1.2:
            return True, f"⏩ Bereits optimal komprimiert ({current_mbps:.1f} Mbps)"

    return False, ""


def build_ffmpeg_cmd(
    src: Path,
    dst: Path,
    video_codec: str,
    target_bitrate: str,
    audio_bitrate: str,
    copy_audio: bool,
) -> List[str]:
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


def compress_videos(cfg: Config) -> None:
    if not which_or_hint("ffmpeg") or not which_or_hint("ffprobe"):
        print("ffmpeg/ffprobe nicht gefunden. Bitte installieren und im PATH verfügbar machen.")
        return

    cfg.target.mkdir(parents=True, exist_ok=True)

    files = collect_files(cfg.source, cfg.recursive)
    print(f"Komprimiere Filme von {cfg.source} nach {cfg.target}")
    print("=" * 60)
    print(f"Gefunden: {len(files)} Video-Dateien")
    print()

    use_videotoolbox = False
    if cfg.codec == "auto":
        use_videotoolbox = detect_videotoolbox()
    elif cfg.codec == "hevc_videotoolbox":
        use_videotoolbox = True
    else:
        use_videotoolbox = False

    video_codec = "hevc_videotoolbox" if use_videotoolbox else "libx265"

    successful = failed = skipped = copied = 0

    for idx, src in enumerate(files, 1):
        # Destination path: always .mp4 for encoded output; preserved for copies
        dst_encoded = (cfg.target / src.with_suffix(".mp4").name)
        dst_copy = cfg.target / src.name

        print(f"[{idx}/{len(files)}] Verarbeite: {src.name}")

        # Skip if output exists and not overwriting
        if not cfg.overwrite and (dst_encoded.exists() or dst_copy.exists()):
            print("   ⏩ Ziel existiert, überspringe (kein Überschreiben)")
            skipped += 1
            print()
            continue

        probe = ffprobe_json(src)
        target_bitrate = pick_target_bitrate(probe.width, cfg)
        target_bitrate_mbps = float(target_bitrate.rstrip("M"))

        do_skip, reason = should_skip_copy(
            src,
            probe,
            cfg.min_size_mb,
            cfg.low_bitrate_threshold_mbps,
            target_bitrate_mbps,
        )

        if do_skip and cfg.copy_original_on_skip:
            print(f"   {reason} – kopiere Original")
            if not cfg.dry_run:
                # choose output path for copy; if encoded file would collide, use copy name
                out = dst_copy
                if not cfg.overwrite and out.exists():
                    skipped += 1
                    print("   ⏩ Ziel existiert, überspringe Kopie")
                    print()
                    continue
                shutil.copy2(src, out)
            skipped += 1
            copied += 1
            print()
            continue

        # Log info
        if probe.width and probe.height:
            print(f"   Auflösung: {probe.width}x{probe.height}, Ziel-Bitrate: {target_bitrate}")
        else:
            print(f"   Auflösung unbekannt, verwende Standard-Bitrate: {target_bitrate}")
        if probe.bitrate_bps:
            print(f"   Aktuelle Bitrate: {probe.bitrate_bps / 1_000_000:.1f} Mbps")

        if cfg.dry_run:
            print("   (Dry-run) Überspringe Encoding")
            skipped += 1
            print()
            continue

        cmd = build_ffmpeg_cmd(
            src,
            dst_encoded,
            video_codec,
            target_bitrate,
            cfg.audio_bitrate,
            cfg.copy_audio,
        )

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and dst_encoded.exists():
                original_size = human_mb(src.stat().st_size)
                compressed_size = human_mb(dst_encoded.stat().st_size)
                reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0.0
                print("✅ Erfolgreich: {}".format(src.name))
                print(
                    f"   Original: {original_size:.1f} MB → Komprimiert: {compressed_size:.1f} MB (-{reduction:.1f}%)"
                )
                successful += 1
            else:
                print(f"❌ Fehler bei: {src.name}")
                stderr_short = (result.stderr or "").strip().splitlines()
                err_preview = " ".join(stderr_short[-3:])[:200]
                print(f"   FFmpeg Fehler: {err_preview} ...")
                failed += 1
                # Clean up partial file if exists
                try:
                    if dst_encoded.exists():
                        dst_encoded.unlink()
                except Exception:
                    pass
        except Exception as e:
            print(f"❌ Fehler bei: {src.name}")
            print(f"   Python Fehler: {e}")
            failed += 1

        print()

    print("=" * 60)
    print("Komprimierung abgeschlossen!")
    print(f"Erfolgreich komprimiert: {successful}")
    print(f"Übersprungen (Original kopiert/ohne Encoding): {skipped}")
    print(f"Fehler: {failed}")
    print(f"Gesamt: {len(files)}")
    print(f"Videos im Zielordner: {successful + copied}")


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Batch-Video-Komprimierung (HEVC)")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("/Volumes/T7/Ahab/AhabPlus/AhabPlus/Kameras/Fuji"),
        help="Quellordner",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("/Volumes/T7/Ahab/AhabPlus/AhabPlus/Kameras/Fuji_compressed"),
        help="Zielordner",
    )
    parser.add_argument("--recursive", action="store_true", help="Unterordner mit einbeziehen")
    parser.add_argument("--min-size", type=float, default=30.0, help="Min. Dateigröße in MB für Encoding")
    parser.add_argument(
        "--low-bitrate-threshold-mbps",
        type=float,
        default=5.0,
        help="Schwelle in Mbps für 'bereits gut komprimiert' <1080p",
    )
    parser.add_argument("--bitrate-4k", default="25M", help="Zielbitrate 4K")
    parser.add_argument("--bitrate-1440p", default="18M", help="Zielbitrate 1440p")
    parser.add_argument("--bitrate-1080p", default="12M", help="Zielbitrate 1080p")
    parser.add_argument("--bitrate-720p", default="8M", help="Zielbitrate 720p und kleiner")
    parser.add_argument("--fallback-bitrate", default="15M", help="Zielbitrate Fallback, wenn Auflösung unbekannt")
    parser.add_argument(
        "--codec",
        choices=["auto", "hevc_videotoolbox", "libx265"],
        default="auto",
        help="Video-Codec Auswahl",
    )
    parser.add_argument("--no-copy-on-skip", action="store_true", help="Bei Skip Original nicht kopieren")
    parser.add_argument("--skip-existing", action="store_true", help="Existierende Zieldateien nicht überschreiben")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, was passieren würde")
    parser.add_argument("--audio-bitrate", default="128k", help="Audio Bitrate für AAC")
    parser.add_argument("--copy-audio", action="store_true", help="Audio unverändert kopieren")

    args = parser.parse_args()
    return Config(
        source=args.source,
        target=args.target,
        recursive=bool(args.recursive),
        min_size_mb=float(args.min_size),
        low_bitrate_threshold_mbps=float(args.low_bitrate_threshold_mbps),
        bitrate_4k=str(args.bitrate_4k),
        bitrate_1440p=str(args.bitrate_1440p),
        bitrate_1080p=str(args.bitrate_1080p),
        bitrate_720p=str(args.bitrate_720p),
        fallback_bitrate=str(args.fallback_bitrate),
        codec=str(args.codec),
        copy_original_on_skip=not args.no_copy_on_skip,
        overwrite=not args.skip_existing,
        dry_run=bool(args.dry_run),
        audio_bitrate=str(args.audio_bitrate),
        copy_audio=bool(args.copy_audio),
    )


if __name__ == "__main__":
    config = parse_args()
    compress_videos(config)
