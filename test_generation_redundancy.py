#!/usr/bin/env python3
"""
Script de prueba para verificar la generación redundante de Flashcards (v2.0).
Simula una sección sobre 'El Dolo' y genera múltiples preguntas atómicas.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.config import ConfigLoader
from src.infrastructure.llm import LLMServiceImpl
from src.infrastructure.llm.prompt_manager import PromptServiceImpl
from src.infrastructure.persistence import ExperimentRepositoryJSON, QuestionRepositoryJSON
from src.application.use_cases.generate_questions import GenerateQuestionsUseCase, GenerateQuestionsRequest
from src.domain.entities.question import QuestionType
from src.domain.entities.section import Section
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.classification import Classification, ClassificationResult

# --- MOCK REPOSITORY ---
class MockSectionRepository:
    def __init__(self, section: Section):
        self.section = section
        
    def get_sections_by_document(self, document_id: str) -> List[Section]:
        return [self.section]
        
    def save(self, section: Section):
        pass
        
    def get_pending_sections(self, document_id: str) -> List[Section]:
        return [self.section]

    def find_relevant(self, document_id: str) -> List[Section]:
        return [self.section]

    def count_total_sections(self, document_id: str) -> int:
        return 1

# --- TEST DATA ---
DOLO_TEXT = """
El dolo consiste en la intención positiva de inferir injuria a la persona o propiedad de otro (Art. 44 CC).
En el ámbito del cumplimiento de las obligaciones, el dolo corresponde a una maquinación fraudulenta destinada a incumplir la obligación.
Actúa como un factor de imputabilidad y agravante de responsabilidad.
El efecto principal es que el deudor doloso responde de todos los perjuicios, tanto previstos como imprevistos, que sean consecuencia directa del incumplimiento (Art. 1558 CC).
A diferencia de la culpa, el dolo no se puede presumir y debe probarse siempre por quien lo alega (Art. 1459 CC), salvo los casos en que la ley expresamente lo presume.
Finalmente, el dolo no puede condonarse anticipadamente; la condonación del dolo futuro no vale y adolece de objeto ilícito.
"""

def main():
    print("🧪 TEST: Redundancia Atómica en Flashcards (v2.0)")
    print("=" * 60)
    
    # 1. Configuración
    loader = ConfigLoader(Path("config.json"))
    settings = loader.load()
    
    # API Key Hardcoded para el test (tomada del contexto anterior)
    api_key = "32b78bb962f7423fbd33368b9a7f375a.97pxeZDls5Jq4Df6APafLuaw"
    provider = "ollama_cloud"
    model_name = "ministral-3:14b-cloud" # Modelo capaz de seguir instrucciones complejas
    
    print(f"🤖 LLM: {model_name}")
    
    # Obtener configuración del proveedor para extraer base_url
    llm_settings = settings.get_llm_settings(provider)
    
    llm_service = LLMServiceImpl.from_config(
        provider=provider,
        api_key=api_key,
        model=model_name,
        temperature=0.3, # Baja temperatura para precisión
        max_tokens=2000,
        base_url=llm_settings.get("base_url") if isinstance(llm_settings, dict) else getattr(llm_settings, "base_url", "https://ollama.com/api")
    )
    
    if not llm_service.verify_connection():
        print("❌ Error de conexión con LLM")
        return

    # 2. Crear Sección Mock
    section = Section(
        id=1,
        document_id="TEST_DOC_001",
        title="El Dolo Civil",
        page=1,
        text=DOLO_TEXT,
        coordinates=Coordinates(0,0,0,0)
    )
    # Marcar como relevante para que no sea filtrada
    classification = ClassificationResult(
        classification=Classification.RELEVANT,
        score=0.95,
        metrics={},
        reason="Concepto legal fundamental"
    )
    section.classify(classification)
    
    mock_repo = MockSectionRepository(section)
    
    # 3. Servicios
    prompt_service = PromptServiceImpl(prompts_path=settings.paths.prompts_dir)
    question_repo = QuestionRepositoryJSON(settings.paths.output_dir)
    experiment_repo = ExperimentRepositoryJSON(settings.paths.experiments_dir)
    
    use_case = GenerateQuestionsUseCase(
        llm_service=llm_service,
        prompt_service=prompt_service,
        section_repository=mock_repo,
        question_repository=question_repo,
        experiment_repository=experiment_repo,
    )
    
    # 4. Ejecutar
    request = GenerateQuestionsRequest(
        document_id="TEST_DOC_001",
        question_type=QuestionType.FLASHCARD,
        batch_size=1
    )
    
    print("\n📝 Texto de entrada:")
    print(f"'{DOLO_TEXT.strip()}'\n")
    print("⏳ Generando preguntas (esto puede tomar unos segundos)...")
    
    result = use_case.execute(request)
    
    # 5. Mostrar Resultados
    if result.success:
        print("\n✅ RESULTADOS (Preguntas Generadas):")
        print("-" * 60)
        
        # Cargar las preguntas generadas (están en memoria en el repositorio si no se persistieran, 
        # pero aquí GenerateQuestionsUseCase las guarda.
        # Truco: el use case devuelve stats, pero podemos inspeccionar el repo o mejor aún, 
        # leer el archivo JSON generado si queremos, pero para simplificar, el repositorio las tiene.)
        
        # Como es una demo, vamos a leer el archivo más reciente de questions
        import json
        output_file = list(settings.paths.output_dir.glob("preguntas_TEST_DOC_001_*.json"))[-1]
        
        with open(output_file, 'r') as f:
            data = json.load(f)
            
        questions = data.get("preguntas", [])
        for i, q in enumerate(questions, 1):
            content = q.get("contenido_tipo", {})
            meta = q.get("sm2_metadata", {})
            print(f"\n[#{i}] Subtipo: {meta.get('subtype', 'N/A')} | Dif: {meta.get('difficulty', 'N/A')}")
            question_text = content.get('anverso') or content.get('frente')
            print(f"❓ P: {question_text}")
            print(f"💡 R: {content.get('reverso')}")
    else:
        print(f"❌ Error: {result.error_message}")

if __name__ == "__main__":
    main()
