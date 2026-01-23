#!/usr/bin/env python3
"""
Cleanup Script - Script de limpieza para archivos generados incrementalmente.

Uso:
    python cleanup.py [--dry-run]

Elimina archivos JSON incrementales obsoletos en datos/procesadas/,
conservando solo la versión más reciente por documento.
"""

import argparse
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

def parse_filename(filename: str) -> Tuple[str, str]:
    """
    Intenta extraer (document_id, timestamp) del nombre del archivo.
    Formato esperado: preguntas_{doc_id}_{timestamp}.json
    """
    # Regex: preguntas_([a-f0-9]+)_(\d{8}_\d{6})\.json
    match = re.match(r"preguntas_([a-f0-9]+)_(\d{8}_\d{6})\.json", filename)
    if match:
        return match.group(1), match.group(2)
    return None, None

def cleanup(dry_run: bool = False):
    # Ruta base
    base_dir = Path("datos/procesadas")
    if not base_dir.exists():
        print(f"❌ Directorio {base_dir} no existe.")
        return

    # Agrupar archivos por document_id
    files_by_doc: Dict[str, List[Path]] = defaultdict(list)
    
    # Escanear
    all_files = list(base_dir.glob("*.json"))
    print(f"📂 Encontrados {len(all_files)} archivos JSON en {base_dir}")

    count_processed = 0
    for file_path in all_files:
        doc_id, timestamp = parse_filename(file_path.name)
        if doc_id and timestamp:
            files_by_doc[doc_id].append(file_path)
            count_processed += 1
    
    print(f"ℹ️  Identificados {count_processed} archivos con formato incremental.")
    print("-" * 40)

    # Procesar grupos
    deleted_count = 0
    kept_count = 0

    for doc_id, file_list in files_by_doc.items():
        # Ordenar por nombre (que incluye timestamp ordenable YYYYMMDD_HHMMSS)
        # Sort descendente (más nuevo primero)
        file_list.sort(key=lambda p: p.name, reverse=True)
        
        # El primero es el más nuevo (Keep)
        newest = file_list[0]
        others = file_list[1:]

        print(f"📄 Documento: {doc_id}")
        print(f"   ✅ Conservar: {newest.name}")
        
        for old in others:
            if dry_run:
                print(f"   🗑️  [DRY RUN] Eliminaría: {old.name}")
            else:
                try:
                    os.remove(old)
                    print(f"   🗑️  Eliminado: {old.name}")
                    deleted_count += 1
                except OSError as e:
                    print(f"   ❌ Error eliminando {old.name}: {e}")

        kept_count += 1
        print("")

    # Resumen
    action = "Detectados para eliminar" if dry_run else "Eliminados"
    print("=" * 40)
    print(f"📊 Resumen:")
    print(f"   Archivos conservados (última versión): {kept_count}")
    print(f"   Archivos {action.lower()}: {deleted_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Limpia archivos JSON incrementales obsoletos.")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin borrar nada.")
    args = parser.parse_args()
    
    cleanup(args.dry_run)
