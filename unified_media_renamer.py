#!/usr/bin/env python3
"""
Unified Media Renamer - Schlanke Version
Intelligente Datei-Umbenennung: Original-Dateien vollständig umbenennen, 
bereits umbenannte nur korrigieren. Nur Osmo/Lumix als Kamera-Namen.
"""

import os
import json
import re
import hashlib
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def install_packages():
    """Installiert benötigte Packages"""
    packages = ['pillow', 'pymediainfo', 'tqdm']
    for package in packages:
        try:
            __import__(package if package != 'pillow' else 'PIL')
        except ImportError:
            print(f"Installiere {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_packages()

from PIL import Image
from PIL.ExifTags import TAGS
from pymediainfo import MediaInfo
from tqdm import tqdm

# Kamera-Mappings: Nur Osmo und Lumix
CAMERA_MAPPINGS = {
    'DJI': 'Osmo',
    'GH5': 'Lumix', 
    'GX80': 'Lumix'
}

def detect_file_status(filename):
    """Erkennt bereits umbenannte Dateien: YYYY-MM-DD_HH-MM-SS_..."""
    pattern = r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[A-Za-z0-9].*\.[a-zA-Z0-9]+$'
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

def detect_camera(metadata, filename, is_renamed):
    """Erkennt Kamera-Typ"""
    if is_renamed:
        parts = filename.split('_')
        return parts[2] if len(parts) >= 3 else 'CAM'
    
    # Original-Dateien: Aus Metadaten + Dateiname
    if 'model' in metadata:
        model = metadata['model']
        if 'DC-GH5' in model:
            return 'GH5'
        elif 'DMC-GX80' in model:
            return 'GX80'
        elif 'PP-101' in model:
            return 'DJI'
    
    if 'make' in metadata:
        make = metadata['make']
        if 'DJI' in make:
            return 'DJI'
        elif 'Panasonic' in make:
            return 'GX80'
    
    # Fallback über Dateiname
    filename_upper = filename.upper()
    if filename_upper.startswith('DJI_'):
        return 'DJI'
    elif filename_upper.startswith('P10'):
        return 'GX80'
    
    return 'CAM'

def extract_number(filename, camera_type, is_renamed):
    """Extrahiert Nummer aus Dateiname"""
    if is_renamed:
        parts = filename.split('_')
        if len(parts) >= 4:
            return Path('_'.join(parts[3:])).stem
        elif len(parts) == 3:
            return Path(parts[2]).stem
        return 'UNKNOWN'
    
    # Original-Dateien
    filename_stem = Path(filename).stem
    
    if camera_type == 'DJI':
        match = re.search(r'_(\d{4})_[A-Z]?$', filename_stem)
        if match:
            return match.group(1)
    elif camera_type in ['GH5', 'GX80']:
        match = re.search(r'(P\d+)', filename_stem)
        if match:
            return match.group(1)
    
    return filename_stem

def generate_filename(file_path, metadata, camera_type, is_renamed):
    """Generiert neuen Dateinamen"""
    original_name = file_path.name
    
    if is_renamed:
        # Korrektur-Modus
        parts = original_name.split('_')
        if len(parts) < 3:
            return original_name
        
        corrected_camera = CAMERA_MAPPINGS.get(parts[2])
        if corrected_camera:
            parts[2] = corrected_camera
        elif parts[2] not in ['Osmo', 'Lumix']:
            # Unbekannte Kamera entfernen
            if len(parts) >= 4:
                parts = [parts[0], parts[1]] + parts[3:]
        
        new_name = '_'.join(parts)
    else:
        # Vollständige Umbenennung
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
        
        # Nummer extrahieren
        number = extract_number(original_name, camera_type, False)
        
        # Name zusammenbauen
        date_str = date_time.strftime('%Y-%m-%d_%H-%M-%S')
        corrected_camera = CAMERA_MAPPINGS.get(camera_type)
        
        if corrected_camera:
            new_name = f"{date_str}_{corrected_camera}_{number}"
        else:
            new_name = f"{date_str}_{number}"
        
        # Extension normalisieren
        ext = file_path.suffix.lower()
        if ext == '.jpeg':
            ext = '.jpg'
        new_name += ext
    
    return new_name

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
        'corrections': []
    }
    
    for file_info in tqdm(files_list, desc="Verarbeite", unit="Datei"):
        try:
            file_path = file_info['path']
            file_type = file_info['type']
            is_renamed = file_info['is_renamed']
            
            # Metadaten nur für Original-Dateien
            metadata = {}
            if not is_renamed:
                metadata = get_metadata(file_path, file_type)
            
            camera_type = detect_camera(metadata, file_path.name, is_renamed)
            new_filename = generate_filename(file_path, metadata, camera_type, is_renamed)
            
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
            
            # Umbenennen
            if not dry_run:
                file_path.rename(new_path)
            
            action = {
                'old_name': file_path.name,
                'new_name': new_filename,
                'camera': camera_type
            }
            
            if is_renamed:
                results['corrections'].append(action)
            else:
                results['renames'].append(action)
            
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
    print("✓ Nur Osmo/Lumix als Kamera-Namen")
    print("✓ Extension-Normalisierung") 
    print("✓ Intelligente Original/Umbenannt-Erkennung")
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
    print(f"  Korrigiert: {len(results['corrections'])}")
    print(f"  Unverändert: {results['unchanged']}")
    print(f"  Fehler: {results['errors']}")
    
    # Beispiele
    if results['renames'][:2]:
        print(f"\nBeispiel Umbenennungen:")
        for r in results['renames'][:2]:
            print(f"  {r['old_name']} → {r['new_name']}")
    
    if results['corrections'][:2]:
        print(f"\nBeispiel Korrekturen:")
        for r in results['corrections'][:2]:
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