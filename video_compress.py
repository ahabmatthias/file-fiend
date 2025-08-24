#!/usr/bin/env python3
import os
import subprocess
import glob
import shutil
from pathlib import Path

def compress_videos():
    # Quell- und Zielordner definieren
    source_dir = "/Volumes/T7/Ahab/AhabPlus/AhabPlus/Kameras/Fuji"
    target_dir = "/Volumes/T7/Ahab/AhabPlus/AhabPlus/Kameras/Fuji_compressed"
    
    # Zielordner erstellen
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Komprimiere Filme von {source_dir} nach {target_dir}")
    print("=" * 60)
    
    # Alle MP4 und MOV Dateien finden
    video_files = []
    video_files.extend(glob.glob(os.path.join(source_dir, "*.mp4")))
    video_files.extend(glob.glob(os.path.join(source_dir, "*.MOV")))
    
    print(f"Gefunden: {len(video_files)} Video-Dateien")
    print()
    
    successful = 0
    failed = 0
    skipped = 0
    copied = 0
    
    for i, file_path in enumerate(video_files, 1):
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(target_dir, f"{name_without_ext}.mp4")
        
        print(f"[{i}/{len(video_files)}] Verarbeite: {filename}")
        
        # Intelligente Bitrate-Wahl basierend auf Auflösung und aktueller Bitrate
        probe_cmd = ["ffprobe", "-v", "quiet", "-select_streams", "v:0", 
                    "-show_entries", "stream=width,height,bit_rate", "-of", "csv=s=x:p=0", file_path]
        try:
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            parts = probe_result.stdout.strip().split('x')
            width = int(parts[0])
            height_and_bitrate = parts[1].split(',')
            height = int(height_and_bitrate[0])
            
            # Versuche aktuelle Bitrate zu ermitteln
            try:
                current_bitrate_bps = int(height_and_bitrate[1]) if len(height_and_bitrate) > 1 else 0
                current_bitrate_mbps = current_bitrate_bps / 1_000_000
            except:
                current_bitrate_mbps = 0
            
            # Dateigröße prüfen
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # Skip-Logik: Kleine Dateien oder bereits niedrige Bitrate
            if file_size_mb < 30:  # Dateien unter 30MB
                print(f"   ⏩ Überspringe kleine Datei ({file_size_mb:.1f} MB) - kopiere Original")
                # Original ins Zielverzeichnis kopieren
                shutil.copy2(file_path, output_path)
                skipped += 1
                copied += 1
                continue
            elif current_bitrate_mbps > 0 and current_bitrate_mbps < 5 and width < 1920:
                print(f"   ⏩ Überspringe bereits gut komprimierte Datei ({current_bitrate_mbps:.1f} Mbps) - kopiere Original")
                # Original ins Zielverzeichnis kopieren
                shutil.copy2(file_path, output_path)
                skipped += 1
                copied += 1
                continue
            
            # Ziel-Bitrate basierend auf Auflösung
            if width >= 3840:  # 4K
                target_bitrate = "25M"
            elif width >= 2560:  # 1440p
                target_bitrate = "18M"
            elif width >= 1920:  # 1080p
                target_bitrate = "12M"
            else:  # 720p und darunter
                target_bitrate = "8M"
            
            # Wenn aktuelle Bitrate bereits niedriger ist als Ziel, überspringe
            target_bitrate_num = int(target_bitrate.replace('M', ''))
            if current_bitrate_mbps > 0 and current_bitrate_mbps <= target_bitrate_num * 1.2:
                print(f"   ⏩ Bereits optimal komprimiert ({current_bitrate_mbps:.1f} Mbps) - kopiere Original")
                # Original ins Zielverzeichnis kopieren
                shutil.copy2(file_path, output_path)
                skipped += 1
                copied += 1
                continue
                
            print(f"   Auflösung: {width}x{height}, Ziel-Bitrate: {target_bitrate}")
            if current_bitrate_mbps > 0:
                print(f"   Aktuelle Bitrate: {current_bitrate_mbps:.1f} Mbps")
            
        except Exception as e:
            # Fallback für sehr kleine Dateien
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb < 30:
                print(f"   ⏩ Überspringe kleine Datei ({file_size_mb:.1f} MB) - kopiere Original")
                # Original ins Zielverzeichnis kopieren
                shutil.copy2(file_path, output_path)
                skipped += 1
                copied += 1
                continue
            target_bitrate = "15M"  # Fallback
            print(f"   Auflösung unbekannt, verwende Standard-Bitrate: {target_bitrate}")

        # FFmpeg Befehl
        cmd = [
            "ffmpeg",
            "-i", file_path,
            "-c:v", "hevc_videotoolbox",
            "-b:v", target_bitrate,
            "-tag:v", "hvc1",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",  # Überschreiben ohne Nachfrage
            output_path
        ]
        
        try:
            # FFmpeg ausführen (ohne Output im Terminal)
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Dateigröße vergleichen
                original_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                compressed_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
                reduction = ((original_size - compressed_size) / original_size) * 100
                
                print(f"✅ Erfolgreich: {filename}")
                print(f"   Original: {original_size:.1f} MB → Komprimiert: {compressed_size:.1f} MB (-{reduction:.1f}%)")
                successful += 1
            else:
                print(f"❌ Fehler bei: {filename}")
                print(f"   FFmpeg Fehler: {result.stderr[:100]}...")
                failed += 1
                
        except Exception as e:
            print(f"❌ Fehler bei: {filename}")
            print(f"   Python Fehler: {str(e)}")
            failed += 1
        
        print()
    
    print("=" * 60)
    print(f"Komprimierung abgeschlossen!")
    print(f"Erfolgreich komprimiert: {successful}")
    print(f"Übersprungen (Original kopiert): {skipped}")
    print(f"Fehler: {failed}")
    print(f"Gesamt: {len(video_files)}")
    print(f"Videos im Zielordner: {successful + copied}")

if __name__ == "__main__":
    compress_videos()