#!/usr/bin/env python3
"""
Script 2: Jahr-Ordner-Organisation
Organisiert bereits umbenannte Dateien in Jahr-Ordner und löscht leere Unterordner
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict

def extract_year_from_filename(filename):
    """Extrahiert das Jahr aus dem Dateinamen (erste 4 Zeichen)"""
    try:
        year_str = filename[:4]
        year = int(year_str)
        
        # Plausibilitätsprüfung (zwischen 1990-2030)
        if 1990 <= year <= 2030:
            return year
        else:
            return None
    except (ValueError, IndexError):
        return None

def collect_files_with_years(folder_path):
    """Sammelt alle Dateien und gruppiert sie nach Jahren"""
    folder = Path(folder_path)
    
    # Unterstützte Dateiformate
    supported_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.heic', 
                           '.mp4', '.mov', '.avi', '.mkv', '.aac', '.wav', '.mp3', '.m4a'}
    
    files_by_year = defaultdict(list)
    invalid_files = []
    
    print("📂 Sammle Dateien und analysiere Jahre...")
    
    all_files = []
    for file_path in folder.rglob('*'):
        if file_path.is_file():
            all_files.append(file_path)
    
    for file_path in tqdm(all_files, desc="Analysiere Dateien", unit="Datei"):
        # Überspringe bestimmte Dateien
        if (file_path.name.startswith('._') or 
            file_path.name == '.DS_Store' or
            file_path.name.startswith('rename_log_') or
            file_path.name.startswith('camera_rename_log_') or
            file_path.parent.name == 'duplicates'):
            continue
        
        extension = file_path.suffix.lower()
        if extension not in supported_extensions:
            continue
        
        # Jahr aus Dateiname extrahieren
        year = extract_year_from_filename(file_path.name)
        
        if year is None:
            invalid_files.append({
                'path': file_path,
                'reason': 'Jahr nicht erkennbar oder ungültig'
            })
            continue
        
        files_by_year[year].append(file_path)
    
    return files_by_year, invalid_files

def find_filename_conflicts(files_by_year, target_folder):
    """Findet Konflikte wenn Dateien mit gleichem Namen in verschiedenen Quell-Ordnern existieren"""
    print("🔍 Prüfe auf Dateiname-Konflikte...")
    
    conflicts = []
    
    for year, files in files_by_year.items():
        year_folder = target_folder / str(year)
        filename_sources = defaultdict(list)
        
        # Gruppiere Dateien nach Dateiname
        for file_path in files:
            filename_sources[file_path.name].append(file_path)
        
        # Prüfe auf Konflikte (gleicher Name, verschiedene Quell-Ordner)
        for filename, file_paths in filename_sources.items():
            if len(file_paths) > 1:
                # Prüfe ob sie aus verschiedenen Ordnern kommen
                source_dirs = set(fp.parent for fp in file_paths)
                if len(source_dirs) > 1:
                    conflicts.append({
                        'filename': filename,
                        'year': year,
                        'paths': file_paths,
                        'source_dirs': list(source_dirs)
                    })
    
    return conflicts

def create_year_folders(files_by_year, target_folder, dry_run=True):
    """Erstellt Jahr-Ordner für alle gefundenen Jahre"""
    years = sorted(files_by_year.keys())
    
    if dry_run:
        print(f"🔍 DRY RUN - Würde {len(years)} Jahr-Ordner erstellen:")
        for year in years:
            print(f"   📁 {year}/ ({len(files_by_year[year])} Dateien)")
    else:
        print(f"📁 Erstelle {len(years)} Jahr-Ordner...")
        for year in years:
            year_folder = target_folder / str(year)
            year_folder.mkdir(exist_ok=True)
            print(f"   ✅ {year}/ ({len(files_by_year[year])} Dateien)")
    
    return years

def move_files_to_year_folders(files_by_year, target_folder, dry_run=True):
    """Verschiebt Dateien in die entsprechenden Jahr-Ordner"""
    total_files = sum(len(files) for files in files_by_year.values())
    moved_files = []
    errors = []
    
    print(f"\n{'🔍 DRY RUN - Würde verschieben:' if dry_run else '📦 Verschiebe Dateien:'}")
    
    for year in sorted(files_by_year.keys()):
        files = files_by_year[year]
        year_folder = target_folder / str(year)
        
        print(f"\n📅 Jahr {year}: {len(files)} Dateien")
        
        for file_path in tqdm(files, desc=f"Jahr {year}", unit="Datei"):
            try:
                target_path = year_folder / file_path.name
                
                # Prüfe ob Zieldatei bereits existiert
                if target_path.exists() and target_path != file_path:
                    errors.append({
                        'file': file_path,
                        'target': target_path,
                        'error': 'Zieldatei existiert bereits'
                    })
                    continue
                
                if not dry_run:
                    # Verschiebe Datei nur wenn sie nicht schon im richtigen Ordner ist
                    if file_path.parent != year_folder:
                        shutil.move(str(file_path), str(target_path))
                
                moved_files.append({
                    'source': file_path,
                    'target': target_path,
                    'year': year
                })
                
            except Exception as e:
                errors.append({
                    'file': file_path,
                    'target': year_folder / file_path.name,
                    'error': str(e)
                })
    
    return moved_files, errors

def find_empty_folders(folder_path, preserve_year_folders=None):
    """Findet leere Ordner (rekursiv), behält aber Jahr-Ordner"""
    folder = Path(folder_path)
    empty_folders = []
    
    if preserve_year_folders is None:
        preserve_year_folders = set()
    
    def is_empty_folder(path):
        if not path.is_dir():
            return False
        
        # Jahr-Ordner niemals als "leer" betrachten
        if path.name.isdigit() and path.parent == folder:
            return False
        
        try:
            # Prüfe ob Ordner nur andere leere Ordner oder System-Dateien enthält
            contents = list(path.iterdir())
            
            for item in contents:
                if item.is_file():
                    # Überspringe System-Dateien
                    if item.name.startswith('._') or item.name == '.DS_Store':
                        continue
                    # Echte Datei gefunden
                    return False
                elif item.is_dir():
                    # Rekursiv prüfen ob Unterordner leer ist
                    if not is_empty_folder(item):
                        return False
            
            return True
        except PermissionError:
            return False
    
    # Sammle alle Ordner
    all_folders = []
    for item in folder.rglob('*'):
        if item.is_dir() and item != folder:
            all_folders.append(item)
    
    # Sortiere nach Tiefe (tiefste zuerst) für korrekte Löschung
    all_folders.sort(key=lambda x: len(x.parts), reverse=True)
    
    for folder_path in all_folders:
        if is_empty_folder(folder_path):
            empty_folders.append(folder_path)
    
    return empty_folders

def remove_empty_folders(empty_folders, dry_run=True):
    """Entfernt leere Ordner"""
    if not empty_folders:
        print("✅ Keine leeren Ordner gefunden!")
        return []
    
    removed_folders = []
    
    if dry_run:
        print(f"🔍 DRY RUN - Würde {len(empty_folders)} leere Ordner löschen:")
        for folder_path in empty_folders:
            print(f"   🗑️  {folder_path}")
    else:
        print(f"🗑️  Lösche {len(empty_folders)} leere Ordner...")
        for folder_path in tqdm(empty_folders, desc="Lösche Ordner", unit="Ordner"):
            try:
                folder_path.rmdir()
                removed_folders.append(folder_path)
                print(f"   ✅ {folder_path}")
            except Exception as e:
                print(f"   ❌ Fehler beim Löschen von {folder_path}: {e}")
    
    return removed_folders

def organize_by_year(folder_path, dry_run=True):
    """Hauptfunktion zur Jahr-Organisation"""
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"❌ Ordner nicht gefunden: {folder_path}")
        return None
    
    # 1. Dateien sammeln und nach Jahren gruppieren
    files_by_year, invalid_files = collect_files_with_years(folder_path)
    
    if not files_by_year:
        print("❌ Keine gültigen Dateien mit Jahr-Information gefunden.")
        return None
    
    total_files = sum(len(files) for files in files_by_year.values())
    print(f"📊 Gefunden: {total_files} Dateien in {len(files_by_year)} Jahren")
    
    if invalid_files:
        print(f"⚠️  {len(invalid_files)} Dateien übersprungen (kein erkennbares Jahr)")
    
    # 2. Prüfung auf Dateiname-Konflikte
    conflicts = find_filename_conflicts(files_by_year, folder)
    
    if conflicts:
        print(f"\n❌ FEHLER: {len(conflicts)} Dateiname-Konflikte gefunden!")
        print("Identische Dateinamen in verschiedenen Quell-Ordnern:")
        for conflict in conflicts[:5]:  # Nur erste 5 anzeigen
            print(f"\n📄 {conflict['filename']} (Jahr {conflict['year']}):")
            for path in conflict['paths']:
                print(f"   - {path}")
        
        if len(conflicts) > 5:
            print(f"   ... und {len(conflicts) - 5} weitere Konflikte")
        
        print("\n❌ Verarbeitung gestoppt! Bitte löse die Konflikte manuell.")
        return None
    
    # 3. Jahr-Ordner erstellen
    years = create_year_folders(files_by_year, folder, dry_run)
    
    # 4. Dateien verschieben
    moved_files, move_errors = move_files_to_year_folders(files_by_year, folder, dry_run)
    
    # 5. Leere Ordner finden und löschen
    empty_folders = find_empty_folders(folder_path, preserve_year_folders=set(map(str, years)))
    removed_folders = remove_empty_folders(empty_folders, dry_run)
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG:")
    print(f"Jahr-Ordner: {len(years)} ({', '.join(map(str, years))})")
    print(f"Verschobene Dateien: {len(moved_files)}")
    print(f"Verschiebe-Fehler: {len(move_errors)}")
    print(f"Übersprungene Dateien: {len(invalid_files)}")
    print(f"Gelöschte leere Ordner: {len(removed_folders)}")
    
    # Details zu Fehlern
    if move_errors:
        print(f"\n⚠️  Verschiebe-Fehler ({len(move_errors)}):")
        for error in move_errors[:5]:
            print(f"   - {error['file'].name}: {error['error']}")
        if len(move_errors) > 5:
            print(f"   ... und {len(move_errors) - 5} weitere")
    
    if invalid_files:
        print(f"\n⚠️  Übersprungene Dateien ({len(invalid_files)}):")
        for invalid in invalid_files[:5]:
            print(f"   - {invalid['path'].name}: {invalid['reason']}")
        if len(invalid_files) > 5:
            print(f"   ... und {len(invalid_files) - 5} weitere")
    
    # Log-Datei speichern
    results = {
        'years': years,
        'moved_files': [{'source': str(mf['source']), 'target': str(mf['target']), 'year': mf['year']} for mf in moved_files],
        'move_errors': [{'file': str(err['file']), 'target': str(err['target']), 'error': err['error']} for err in move_errors],
        'invalid_files': [{'file': str(inv['path']), 'reason': inv['reason']} for inv in invalid_files],
        'removed_folders': [str(rf) for rf in removed_folders],
        'timestamp': datetime.now().isoformat()
    }
    
    output_file = folder / f"year_organization_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Detaillierte Ergebnisse gespeichert in: {output_file.name}")
    
    return results

if __name__ == "__main__":
    # Ordner-Pfad (passe hier an)
    folder_path = "/Volumes/T7/Filmkram Backup Kopie"
    
    print("Script 2: Jahr-Ordner-Organisation")
    print("=" * 50)
    print("Organisiert Dateien in Jahr-Ordner und löscht leere Unterordner")
    print()
    
    # Erst DRY RUN
    print("🔍 TESTE JAHR-ORGANISATION (Dry Run)")
    results = organize_by_year(folder_path, dry_run=True)
    
    if results:
        print("\n" + "=" * 50)
        if results.get('move_errors'):
            print("⚠️  Es gab Fehler beim Verschieben. Log-Datei prüfen!")
        
        answer = input("Jahr-Organisation durchführen? (j/n): ").lower().strip()
        
        if answer in ['j', 'ja', 'y', 'yes']:
            print("\n✅ FÜHRE JAHR-ORGANISATION DURCH")
            organize_by_year(folder_path, dry_run=False)
        else:
            print("❌ Jahr-Organisation abgebrochen.")
    else:
        print("❌ Jahr-Organisation nicht möglich (Konflikte oder keine Dateien).")