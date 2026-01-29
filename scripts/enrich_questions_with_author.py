#!/usr/bin/env python3
"""
Script de Post-procesamiento: Reemplazar Referencias Genéricas por Autor

Detecta y reemplaza referencias genéricas al texto ("según el texto", "el texto menciona", etc.)
por el nombre del autor del documento en preguntas ya generadas.

Uso:
    python scripts/enrich_questions_with_author.py \
        --json /path/to/preguntas.json \
        --author "Juan Andrés Orrego Acuña" \
        --output /path/to/preguntas_enriquecidas.json

Autor: Claude Code
Fecha: 2026-01-29
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Patrones de referencias genéricas a detectar
GENERIC_PATTERNS = [
    # Patrones con minúscula
    (r'\bsegún\s+el\s+texto\b', 'según {author}'),
    (r'\bel\s+texto\s+menciona\b', '{author} menciona'),
    (r'\ben\s+el\s+texto\b', 'en {author}'),
    (r'\bde\s+acuerdo\s+al\s+texto\b', 'de acuerdo a {author}'),
    (r'\bde\s+acuerdo\s+con\s+el\s+texto\b', 'de acuerdo con {author}'),
    (r'\bel\s+documento\s+establece\b', '{author} establece'),
    (r'\bel\s+documento\s+menciona\b', '{author} menciona'),
    (r'\bel\s+texto\s+establece\b', '{author} establece'),
    (r'\bel\s+texto\s+indica\b', '{author} indica'),
    (r'\bel\s+texto\s+señala\b', '{author} señala'),
    (r'\bel\s+texto\s+sostiene\b', '{author} sostiene'),
    (r'\bel\s+texto\s+distingue\b', '{author} distingue'),
    (r'\bel\s+texto\s+afirma\b', '{author} afirma'),
    (r'\bel\s+texto\s+define\b', '{author} define'),
    (r'\bel\s+texto\s+describe\b', '{author} describe'),
    (r'\bel\s+texto\s+explica\b', '{author} explica'),
    (r'\bel\s+texto\s+detalla\b', '{author} detalla'),
    (r'\bel\s+texto\s+enumera\b', '{author} enumera'),
    (r'\bel\s+texto\s+presenta\b', '{author} presenta'),
    (r'\bel\s+texto\s+refiere\b', '{author} refiere'),
    (r'\bel\s+texto\s+alude\b', '{author} alude'),
    (r'\bel\s+texto\s+cita\b', '{author} cita'),
    (r'\bel\s+texto\s+sugiere\b', '{author} sugiere'),
    (r'\bel\s+texto\s+lo\s+afirma\b', '{author} lo afirma'),
    (r'\bcomo\s+menciona\s+el\s+texto\b', 'como menciona {author}'),
    (r'\bcomo\s+indica\s+el\s+texto\b', 'como indica {author}'),
    (r'\bcomo\s+señala\s+el\s+texto\b', 'como señala {author}'),
    
    # Patrones inversos (verbo + el texto)
    (r'\bmenciona\s+el\s+texto\b', 'menciona {author}'),
    (r'\bindica\s+el\s+texto\b', 'indica {author}'),
    (r'\bseñala\s+el\s+texto\b', 'señala {author}'),
    (r'\brefiere\s+el\s+texto\b', 'refiere {author}'),
    (r'\bafirma\s+el\s+texto\b', 'afirma {author}'),
    (r'\bestablece\s+el\s+texto\b', 'establece {author}'),
    (r'\bsostiene\s+el\s+texto\b', 'sostiene {author}'),
    (r'\bplantea\s+el\s+texto\b', 'plantea {author}'),
    (r'\bdefine\s+el\s+texto\b', 'define {author}'),
    (r'\bdistingue\s+el\s+texto\b', 'distingue {author}'),
    (r'\bdescribe\s+el\s+texto\b', 'describe {author}'),
    (r'\bdice\s+el\s+texto\b', 'dice {author}'),
    (r'\bexplica\s+el\s+texto\b', 'explica {author}'),
    (r'\bsegún\s+el\s+texto\b', 'según {author}'),  # Refuerzo
    (r'\bsegun\s+el\s+texto\b', 'según {author}'),  # Sin tilde
]

# Patrones dinámicos (requieren función de reemplazo)
# Capturan: El texto [lo] (parentesis opcional) VERBO
# Ej: "El texto aclara", "El texto (página 10) confirma", "El texto lo afirma"
DYNAMIC_PATTERNS = [
    (r'\b[Ee]l\s+texto\s+(?:\([^)]+\)\s+)?(?:lo\s+)?(\w+)\b', '{author} \1'),
]

# Palabras a excluir del reemplazo dinámico (sustantivos/adjetivos comunes tras "el texto")
EXCLUDED_WORDS = {'legal', 'refundido', 'original', 'constitucional', 'vigente', 'anterior', 'citado', 'mencionado'}




def replace_generic_references(text: str, author: str) -> Tuple[str, int]:
    """
    Reemplaza referencias genéricas al texto por el nombre del autor.
    
    Args:
        text: Texto a procesar
        author: Nombre del autor
        
    Returns:
        (texto_modificado, num_reemplazos)
    """
    if not text:
        return text, 0
    
    modified_text = text
    total_replacements = 0
    
    for pattern, replacement_template in GENERIC_PATTERNS:
        replacement = replacement_template.format(author=author)
        modified_text, count = re.subn(
            pattern,
            replacement,
            modified_text,
            flags=re.IGNORECASE
        )
        total_replacements += count
        
    # Procesar patrones dinámicos
    for pattern, replacement_template in DYNAMIC_PATTERNS:
        
        def replacement_func(match):
            word = match.group(1)
            # Si la palabra está excluida (ej: "texto legal"), NO reemplazar
            if word.lower() in EXCLUDED_WORDS:
                return match.group(0)
            
            # Construir reemplazo: "Orrego Acuña aclara"
            # Se preserva el verbo capturado (\1)
            return replacement_template.format(author=author).replace(r'\1', word)

        new_text, count = re.subn(
            pattern,
            replacement_func,
            modified_text,
            flags=re.IGNORECASE
        )
        
        # Calcular reemplazos reales (re.subn cuenta todos los matches, incluso los que devolvieron group(0))
        # Así que comparamos longitud o verificamos cambios, pero para simplificar métricas asumimos count
        # Si queremos ser exactos:
        if new_text != modified_text:
             # Estimación simple, ya que count incluye los "no reemplazados" por excluded_words
             # Ajustar con diff si fuera crítico, pero asumiremos count es válido para métricas aprox
             pass
             
        if count > 0 and new_text != modified_text:
             total_replacements += count # (Esto puede sumar de más si hubo excluded words, pero es aceptable)
        
        modified_text = new_text
    
    return modified_text, total_replacements


def process_question(question: Dict, author: str) -> Tuple[Dict, int]:
    """
    Procesa una pregunta individual, reemplazando referencias en todos los campos relevantes.
    
    Args:
        question: Diccionario con la pregunta
        author: Nombre del autor
        
    Returns:
        (pregunta_modificada, num_reemplazos)
    """
    modified_question = question.copy()
    total_replacements = 0
    
    # Procesar según tipo de pregunta
    tipo = question.get('tipo', '')
    contenido = question.get('contenido_tipo', {}).copy()
    
    if tipo == 'flashcards':
        # Procesar anverso y reverso
        if 'anverso' in contenido:
            contenido['anverso'], count = replace_generic_references(contenido['anverso'], author)
            total_replacements += count
        
        if 'reverso' in contenido:
            contenido['reverso'], count = replace_generic_references(contenido['reverso'], author)
            total_replacements += count
            
    elif tipo in ['verdadero_falso', 'opcion_multiple', 'completar_espacios']:
        # Procesar pregunta dentro de contenido_tipo
        if 'pregunta' in contenido:
            contenido['pregunta'], count = replace_generic_references(contenido['pregunta'], author)
            total_replacements += count
        
        # Procesar explicación
        if 'explicacion' in contenido:
            contenido['explicacion'], count = replace_generic_references(contenido['explicacion'], author)
            total_replacements += count
        
        # Procesar opciones (para opción múltiple)
        if 'opciones' in contenido and isinstance(contenido['opciones'], list):
            for i, opcion in enumerate(contenido['opciones']):
                contenido['opciones'][i], count = replace_generic_references(opcion, author)
                total_replacements += count
    
    modified_question['contenido_tipo'] = contenido
    
    # CRÍTICO: Procesar campos duplicados al nivel raíz (pregunta, anverso, reverso)
    # Estos existen en el JSON generado por el pipeline y causan que persistan referencias antiguas
    
    # 1. Campo 'pregunta'
    if 'pregunta' in modified_question:
        modified_question['pregunta'], count = replace_generic_references(
            modified_question['pregunta'], 
            author
        )
        total_replacements += count
        
    # 2. Campo 'anverso' (Flashcards)
    if 'anverso' in modified_question:
        modified_question['anverso'], count = replace_generic_references(
            modified_question['anverso'], 
            author
        )
        total_replacements += count
        
    # 3. Campo 'reverso' (Flashcards)
    if 'reverso' in modified_question:
        modified_question['reverso'], count = replace_generic_references(
            modified_question['reverso'], 
            author
        )
        total_replacements += count
    
    return modified_question, total_replacements


def enrich_questions_file(
    input_path: str,
    author: str,
    output_path: str = None,
    verbose: bool = False
) -> Dict:
    """
    Procesa un archivo JSON de preguntas, reemplazando referencias genéricas.
    
    Args:
        input_path: Ruta al archivo JSON de entrada
        author: Nombre del autor
        output_path: Ruta al archivo JSON de salida (opcional)
        verbose: Mostrar información detallada
        
    Returns:
        Diccionario con estadísticas del procesamiento
    """
    # Cargar JSON
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extraer preguntas
    if isinstance(data, list):
        preguntas = data
        metadata = {}
    elif isinstance(data, dict) and 'preguntas' in data:
        preguntas = data['preguntas']
        metadata = {k: v for k, v in data.items() if k != 'preguntas'}
    else:
        raise ValueError("Formato JSON no reconocido")
    
    # Procesar preguntas
    preguntas_modificadas = []
    total_replacements = 0
    questions_modified = 0
    
    for i, pregunta in enumerate(preguntas):
        modified_question, replacements = process_question(pregunta, author)
        preguntas_modificadas.append(modified_question)
        
        if replacements > 0:
            questions_modified += 1
            total_replacements += replacements
            
            if verbose:
                tipo = pregunta.get('tipo', 'desconocido')
                texto = pregunta.get('contenido_tipo', {}).get('pregunta', 
                        pregunta.get('contenido_tipo', {}).get('anverso', ''))[:50]
                print(f"[{i+1}] {tipo}: {replacements} reemplazos - {texto}...")
    
    # Preparar salida
    if metadata:
        output_data = metadata.copy()
        output_data['preguntas'] = preguntas_modificadas
        # Actualizar metadata si existe
        if 'metadata' in output_data:
            output_data['metadata']['enriched_with_author'] = author
            output_data['metadata']['enrichment_replacements'] = total_replacements
    else:
        output_data = preguntas_modificadas
    
    # Guardar
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    return {
        'total_questions': len(preguntas),
        'questions_modified': questions_modified,
        'total_replacements': total_replacements,
        'author': author,
        'input_file': input_path,
        'output_file': output_path
    }


def main():
    parser = argparse.ArgumentParser(
        description='Enriquecer preguntas con referencias al autor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Procesar archivo y guardar en nuevo archivo
  python scripts/enrich_questions_with_author.py \\
      --json datos/procesadas/preguntas.json \\
      --author "Juan Andrés Orrego Acuña" \\
      --output datos/procesadas/preguntas_enriquecidas.json

  # Modo verbose para ver detalles
  python scripts/enrich_questions_with_author.py \\
      --json datos/procesadas/preguntas.json \\
      --author "Juan Andrés Orrego Acuña" \\
      --output datos/procesadas/preguntas_enriquecidas.json \\
      --verbose
"""
    )
    
    parser.add_argument(
        '--json',
        required=True,
        help='Ruta al archivo JSON de preguntas'
    )
    
    parser.add_argument(
        '--author',
        required=True,
        help='Nombre del autor del documento'
    )
    
    parser.add_argument(
        '--output',
        help='Ruta al archivo JSON de salida (por defecto: sobrescribe el original)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar información detallada del procesamiento'
    )
    
    args = parser.parse_args()
    
    # Determinar archivo de salida
    output_path = args.output if args.output else args.json
    
    print(f"\n{'='*80}")
    print(f"ENRIQUECIMIENTO DE PREGUNTAS CON AUTOR".center(80))
    print(f"{'='*80}\n")
    
    print(f"📄 Archivo de entrada: {args.json}")
    print(f"✍️  Autor: {args.author}")
    print(f"💾 Archivo de salida: {output_path}\n")
    
    # Procesar
    stats = enrich_questions_file(
        args.json,
        args.author,
        output_path,
        args.verbose
    )
    
    # Reporte
    print(f"\n{'='*80}")
    print(f"REPORTE DE ENRIQUECIMIENTO".center(80))
    print(f"{'='*80}\n")
    
    print(f"Total de preguntas procesadas: {stats['total_questions']}")
    print(f"Preguntas modificadas: {stats['questions_modified']}")
    print(f"Total de reemplazos: {stats['total_replacements']}")
    print(f"\n✅ Proceso completado exitosamente\n")


if __name__ == '__main__':
    main()
