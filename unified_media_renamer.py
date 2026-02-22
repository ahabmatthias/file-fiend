#!/usr/bin/env python3
"""
Unified Media Renamer - Schlanke Version
Benennt Mediendateien nach Schema YYYY-MM-DD_HHMMSS_<original-stem>.<ext> um.
Bereits umbenannte Dateien (Muster erkannt) werden übersprungen.
"""

import os
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS
from pymediainfo import MediaInfo
from tqdm import tqdm

def detect_file_status(filename):
    """Erkennt bereits umbenannte Dateien: YYYY-MM-DD_HHMMSS_... oder altes Format YYYY-MM-DD_HH-MM-SS_..."""
    pattern = r'^\d{4}-\d{2}-\d{2}_(?:\d{2}-\d{2}-\d{2}|\d{6})_[A-Za-z0-9].*\.[a-zA-Z0-9]+$'
    return re.match(pattern, filename) is not None

def get_metadata(file_path, file_type):
    """Extrahiert Metadaten aus Bild/Video"""
    try:
        if file_type == 'image':
            with Image.open(file_path) as image:
                exif_data = image._getexif()
                if not exif_data:
                    return {}
                
                metadata = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        try:
                            metadata['datetime'] = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                        except:
                            pass
                    elif tag == 'DateTime' and 'datetime' not in metadata:
                        try:
                            metadata['datetime'] = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                        except:
                            pass
                    elif tag in ['Make', 'Model']:
                        metadata[tag.lower()] = str(value)
                return metadata
        
        elif file_type == 'video':
            media_info = MediaInfo.parse(file_path)
            metadata = {}
            for track in media_info.tracks:
                if track.track_type == 'General' and track.recorded_date:
                    try:
                        date_str = str(track.recorded_date)[:19]
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                metadata['datetime'] = datetime.strptime(date_str, fmt)
                                break
                            except:
                                continue
                    except:
                        pass
            return metadata
    except:
        pass
    return {}

def generate_filename(file_path, metadata):
    """Generiert neuen Dateinamen: YYYY-MM-DD_HHMMSS_<original-stem>.<ext>"""
    original_name = file_path.name

    # Datum bestimmen
    date_time = None

    # 1. Aus Dateiname (YYYY-MM-DD)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', original_name)
    if date_match:
        try:
            date_time = datetime.strptime(date_match.group(1) + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        except:
            pass

    # 2. Aus Metadaten
    if not date_time and 'datetime' in metadata:
        date_time = metadata['datetime']

    # 3. Dateisystem-Datum
    if not date_time:
        date_time = datetime.fromtimestamp(file_path.stat().st_mtime)

    date_str = date_time.strftime('%Y-%m-%d_%H%M%S')
    stem = Path(original_name).stem
    ext = file_path.suffix.lower()
    if ext == '.jpeg':
        ext = '.jpg'

    return f"{date_str}_{stem}{ext}"

def find_duplicates(files_list):
    """Einfache Duplikat-Erkennung"""
    print("🔍 Suche nach Duplikaten...")
    
    file_groups = {}
    for file_info in tqdm(files_list, desc="Analysiere", unit="Datei"):
        try:
            file_path = file_info['path']
            key = (file_path.stem, file_path.stat().st_size)
            
            if key not in file_groups:
                file_groups[key] = []
            file_groups[key].append(file_info)
        except:
            continue
    
    duplicates = []
    for group in file_groups.values():
        if len(group) > 1:
            # Älteste behalten, Rest als Duplikat
            group.sort(key=lambda x: x['path'].stat().st_mtime)
            duplicates.extend(group[1:])
    
    if duplicates:
        print(f"⚠️  {len(duplicates)} Duplikate gefunden")
    else:
        print("✅ Keine Duplikate")
    
    return duplicates

def collect_files(folder_path):
    """Sammelt alle Medien-Dateien"""
    folder = Path(folder_path)
    extensions = {'.jpg', '.jpeg', '.png', '.heic', '.mp4', '.mov', '.avi'}
    files = []
    
    print("📂 Sammle Dateien...")
    for file_path in folder.rglob('*'):
        if (file_path.is_file() and 
            file_path.suffix.lower() in extensions and
            not file_path.name.startswith('._') and
            file_path.name != '.DS_Store'):
            
            is_renamed = detect_file_status(file_path.name)
            file_type = 'image' if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.heic'} else 'video'
            
            files.append({
                'path': file_path,
                'type': file_type,
                'is_renamed': is_renamed
            })
    
    return files

def process_files(files_list, dry_run=True):
    """Verarbeitet alle Dateien"""
    results = {
        'processed': 0,
        'unchanged': 0,
        'errors': 0,
        'renames': [],
    }

    for file_info in tqdm(files_list, desc="Verarbeite", unit="Datei"):
        try:
            file_path = file_info['path']
            file_type = file_info['type']
            is_renamed = file_info['is_renamed']

            # Bereits umbenannte Dateien überspringen
            if is_renamed:
                results['unchanged'] += 1
                continue

            metadata = get_metadata(file_path, file_type)
            new_filename = generate_filename(file_path, metadata)

            if new_filename == file_path.name:
                results['unchanged'] += 1
                continue

            new_path = file_path.parent / new_filename

            # Kollision vermeiden
            counter = 1
            while new_path.exists():
                name_parts = new_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_filename = f"{name_parts[0]}_({counter}).{name_parts[1]}"
                else:
                    new_filename = f"{new_filename}_({counter})"
                new_path = file_path.parent / new_filename
                counter += 1

            if not dry_run:
                file_path.rename(new_path)

            results['renames'].append({
                'old_name': file_path.name,
                'new_name': new_filename,
            })
            results['processed'] += 1

        except Exception as e:
            results['errors'] += 1
            print(f"Fehler bei {file_info['path'].name}: {e}")

    return results

def main():
    # PFAD HIER ANPASSEN:
    folder_path = '/Volumes/T7/Alte Platte/Filme/Familie'
    
    print("🎬 Unified Media Renamer (Schlanke Version)")
    print("=" * 50)
    print("✓ Schema: YYYY-MM-DD_HHMMSS_<original-stem>.<ext>")
    print("✓ Extension-Normalisierung")
    print("✓ Bereits umbenannte Dateien werden übersprungen")
    print()
    
    # Dateien sammeln
    files = collect_files(folder_path)
    if not files:
        print("❌ Keine Dateien gefunden")
        return
    
    original_files = [f for f in files if not f['is_renamed']]
    renamed_files = [f for f in files if f['is_renamed']]
    
    print(f"📊 {len(files)} Dateien gefunden:")
    print(f"   Original: {len(original_files)} (vollständig umbenennen)")
    print(f"   Umbenannt: {len(renamed_files)} (nur korrigieren)")
    
    # Duplikate behandeln
    duplicates = find_duplicates(files)
    if duplicates:
        duplicate_paths = {d['path'] for d in duplicates}
        files = [f for f in files if f['path'] not in duplicate_paths]
        print(f"✅ {len(files)} Dateien nach Duplikat-Bereinigung")
    
    if not files:
        print("❌ Keine Dateien zu verarbeiten")
        return
    
    # DRY RUN
    print("\n🔍 DRY RUN...")
    results = process_files(files, dry_run=True)
    
    print(f"\nErgebnis:")
    print(f"  Umbenannt: {len(results['renames'])}")
    print(f"  Unverändert: {results['unchanged']}")
    print(f"  Fehler: {results['errors']}")

    if results['renames'][:2]:
        print(f"\nBeispiel Umbenennungen:")
        for r in results['renames'][:2]:
            print(f"  {r['old_name']} → {r['new_name']}")
    
    # Bestätigung
    if results['processed'] > 0:
        answer = input(f"\n{results['processed']} Dateien verarbeiten? (j/n): ")
        if answer.lower() in ['j', 'ja', 'y', 'yes']:
            print("\n✅ VERARBEITUNG LÄUFT...")
            final_results = process_files(files, dry_run=False)
            
            # Log speichern
            log_file = Path(folder_path) / f"rename_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(final_results, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Fertig! Log: {log_file.name}")
        else:
            print("❌ Abgebrochen")
    else:
        print("✅ Alle Dateien bereits korrekt!")

if __name__ == "__main__":
    main()