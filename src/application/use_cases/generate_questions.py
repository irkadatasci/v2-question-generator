"""
Generate Questions Use Case - Genera preguntas usando LLM.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json

from ...domain.entities.section import Section
from ...domain.entities.question import Question, QuestionType
from ...domain.entities.batch import Batch
from ..ports.services import LLMService, PromptService
from ..ports.repositories import SectionRepository, QuestionRepository, ExperimentRepository


@dataclass
class GenerateQuestionsRequest:
    """Request para generar preguntas."""
    document_id: str
    question_type: QuestionType
    batch_size: int = 5
    only_relevant: bool = True
    auto_adjust_batch_size: bool = True
    save_batches: bool = True
    experiment_tags: Optional[dict] = None


@dataclass
class GenerateQuestionsResult:
    """Resultado de la generación."""
    success: bool
    experiment_id: str = ""
    total_sections: int = 0
    total_batches: int = 0
    batches_successful: int = 0
    batches_failed: int = 0
    questions_generated: int = 0
    questions_valid: int = 0
    questions_invalid: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    output_json_path: Optional[Path] = None
    error_message: str = ""
    execution_time_seconds: float = 0.0


class GenerateQuestionsUseCase:
    """
    Caso de uso: Generar preguntas usando LLM.

    Procesa secciones en batches, envía a LLM con prompts
    especializados y valida las respuestas.

    Etapa 3 del pipeline.
    """

    def __init__(
        self,
        llm_service: LLMService,
        prompt_service: PromptService,
        section_repository: SectionRepository,
        question_repository: QuestionRepository,
        experiment_repository: ExperimentRepository,
    ):
        """
        Args:
            llm_service: Servicio de LLM
            prompt_service: Servicio de prompts
            section_repository: Repositorio de secciones
            question_repository: Repositorio de preguntas
            experiment_repository: Repositorio de experimentos
        """
        self._llm = llm_service
        self._prompts = prompt_service
        self._sections = section_repository
        self._questions = question_repository
        self._experiments = experiment_repository

    def execute(self, request: GenerateQuestionsRequest) -> GenerateQuestionsResult:
        """
        Ejecuta la generación de preguntas.

        Args:
            request: Request con parámetros de generación

        Returns:
            GenerateQuestionsResult con el resultado
        """
        start_time = datetime.now()

        try:
            # 1. Verificar conexión con LLM
            if not self._llm.verify_connection():
                return GenerateQuestionsResult(
                    success=False,
                    error_message=f"No se pudo conectar con {self._llm.provider_name}",
                )

            # 2. Obtener secciones a procesar
            if request.only_relevant:
                sections = self._sections.find_relevant(request.document_id)
            else:
                sections = self._sections.find_all(request.document_id)

            if not sections:
                return GenerateQuestionsResult(
                    success=False,
                    error_message="No hay secciones para procesar",
                )

            # 3. Ajustar batch_size si es necesario
            batch_size = request.batch_size
            if request.auto_adjust_batch_size:
                batch_size = self._calculate_optimal_batch_size(sections)

            # 4. Iniciar experimento
            experiment_id = self._experiments.create(
                llm_provider=self._llm.provider_name,
                model=self._llm.model_name,
                batch_size=batch_size,
                question_type=request.question_type.value,
                prompt_version=self._prompts.get_current_version(request.question_type),
                source_hash=request.document_id,
                tags=request.experiment_tags,
            )

            # 5. Crear batches
            batches = self._create_batches(sections, batch_size)

            # 6. Procesar batches
            all_questions: List[Question] = []
            total_tokens = 0
            total_cost = 0.0
            batches_successful = 0
            batches_failed = 0

            system_prompt = self._prompts.get_system_prompt(request.question_type)

            for batch in batches:
                batch.start_processing()

                try:
                    # Construir prompt para el batch
                    user_prompt = self._prompts.build_user_prompt(
                        sections=batch.sections,
                        question_type=request.question_type,
                    )

                    # DEBUG: Print user prompt
                    print(f"=== USER PROMPT ===")
                    print(user_prompt)
                    print(f"=== END USER PROMPT ===\n")

                    # Llamar a LLM
                    response = self._llm.generate(
                        prompt=user_prompt,
                        system_prompt=system_prompt,
                        response_format="json",
                    )

                    # DEBUG: Print raw response
                    print(f"=== RAW LLM RESPONSE ===")
                    print(f"Response content: {response.content}")
                    print(f"Response type: {type(response.content)}")
                    print(f"Response tokens: {response.tokens_total}")
                    print(f"=== END RAW LLM RESPONSE ===\n")

                    # Parsear respuesta
                    questions = self._parse_response(
                        response.content,
                        request.question_type,
                        batch.sections,
                        request.document_id,
                    )

                    # DEBUG: Print parsing results
                    print(f"=== PARSING RESULTS ===")
                    print(f"Questions parsed: {len(questions)}")
                    for i, q in enumerate(questions):
                        print(f"Question {i+1}: {q}")
                    print(f"=== END PARSING RESULTS ===\n")

                    # Validar preguntas
                    for q in questions:
                        q.validate()

                    # Completar batch
                    batch.complete(
                        questions=questions,
                        tokens_used=response.tokens_total,
                        cost_usd=response.cost_usd,
                        processing_time=response.latency_seconds,
                    )

                    all_questions.extend(questions)
                    total_tokens += response.tokens_total
                    total_cost += response.cost_usd
                    batches_successful += 1

                except Exception as e:
                    print(f"ERROR in batch processing: {e}")
                    batch.fail(str(e))
                    batches_failed += 1

            # 7. Guardar preguntas
            self._questions.save_all(all_questions)

            # 8. Calcular estadísticas finales
            valid_questions = [q for q in all_questions if q.status.value == "validated"]
            invalid_questions = [q for q in all_questions if q.status.value == "invalid"]

            # 9. Actualizar experimento
            execution_time = (datetime.now() - start_time).total_seconds()
            self._experiments.update_results(
                experiment_id=experiment_id,
                total_questions=len(all_questions),
                valid_questions=len(valid_questions),
                execution_time_seconds=execution_time,
                total_cost_usd=total_cost,
                tokens_used=total_tokens,
            )
            self._experiments.complete(experiment_id)

            # 10. Exportar a JSON
            output_json = self._questions.export_to_json(
                output_path=Path(f"datos/procesadas/preguntas_{request.document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"),
                format="internal",
            )

            return GenerateQuestionsResult(
                success=True,
                experiment_id=experiment_id,
                total_sections=len(sections),
                total_batches=len(batches),
                batches_successful=batches_successful,
                batches_failed=batches_failed,
                questions_generated=len(all_questions),
                questions_valid=len(valid_questions),
                questions_invalid=len(invalid_questions),
                tokens_used=total_tokens,
                cost_usd=total_cost,
                output_json_path=output_json,
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            return GenerateQuestionsResult(
                success=False,
                error_message=f"Error en generación: {e}",
            )

    def _calculate_optimal_batch_size(self, sections: List[Section]) -> int:
        """
        Calcula el batch size óptimo basado en las secciones.

        Estrategia basada en P90 de longitudes:
        - P90 > 5000 → batch_size = 2
        - P90 > 3000 → batch_size = 3
        - P90 > 1500 → batch_size = 5
        - P90 <= 1500 → batch_size = 10
        """
        lengths = sorted([s.text_length for s in sections])
        p90_index = int(len(lengths) * 0.90)
        p90 = lengths[p90_index] if p90_index < len(lengths) else lengths[-1]

        if p90 > 5000:
            return 2
        elif p90 > 3000:
            return 3
        elif p90 > 1500:
            return 5
        else:
            return 10

    def _create_batches(self, sections: List[Section], batch_size: int) -> List[Batch]:
        """Crea batches de secciones."""
        batches = []
        for i in range(0, len(sections), batch_size):
            batch_sections = sections[i:i + batch_size]
            batch = Batch.create(batch_id=len(batches), sections=batch_sections)
            batches.append(batch)
        return batches

    def _parse_response(
        self,
        content: any,
        question_type: QuestionType,
        sections: List[Section],
        document_id: str,
    ) -> List[Question]:
        """
        Parsea la respuesta del LLM y crea objetos Question.

        Este método debe ser robusto para manejar diferentes formatos
        de respuesta del LLM, incluyendo modelos de razonamiento (Thinking).
        """
        print(f"=== PARSING DEBUG ===")
        
        questions = []

        # Si el contenido es string, intentar parsear como JSON
        if isinstance(content, str):
            # 1. Limpiar etiquetas de razonamiento (Thinking models como DeepSeek o Ministral)
            if "<thought>" in content:
                import re
                print("Detected <thought> tags, removing them...")
                content = re.sub(r'<thought>.*?</thought>', '', content, flags=re.DOTALL)
            
            # 2. Intentar parseo directo
            processed_content = None
            try:
                processed_content = json.loads(content.strip())
            except json.JSONDecodeError:
                # 3. Intentar extraer de bloques markdown
                json_str = ""
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0]
                
                if json_str:
                    try:
                        processed_content = json.loads(json_str.strip())
                    except json.JSONDecodeError:
                        processed_content = None
                else:
                    # 4. Búsqueda agresiva de { ... } o [ ... ]
                    import re
                    # Buscar el bloque JSON más grande
                    match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
                    if match:
                        try:
                            processed_content = json.loads(match.group(0))
                        except json.JSONDecodeError:
                            processed_content = None
                    else:
                        processed_content = None

            if processed_content is None:
                print(f"Failed to parse content as JSON: {content[:200]}...")
                return []
            content = processed_content
        
        # Extraer lista de preguntas
        if isinstance(content, dict):
            # Buscar en 'preguntas', 'questions' o si el dict mismo contiene una lista
            preguntas_raw = content.get("preguntas", content.get("questions", []))
            if not preguntas_raw and any(isinstance(v, list) for v in content.values()):
                # Si no hay 'preguntas', pero hay alguna lista, tomar la primera
                for v in content.values():
                    if isinstance(v, list):
                        preguntas_raw = v
                        break
        elif isinstance(content, list):
            preguntas_raw = content
        else:
            print(f"Content is neither dict nor list after parsing")
            return []

        if not preguntas_raw:
            print("No questions found in content")
            return []

        # Crear objetos Question
        from ...domain.value_objects.origin import Origin
        from ...domain.value_objects.metadata import QuestionMetadata

        for i, preg in enumerate(preguntas_raw):
            try:
                # Construir Origin
                origen_data = preg.get("origen", preg.get("origin", {}))
                
                # FIX: Mapear section_id relativo (1..N) del batch a section_id absoluto de la DB
                # El LLM ve "Sección 1", "Sección 2" en el prompt, por lo que devuelve 1, 2...
                raw_section_id = origen_data.get("section_id")
                
                if isinstance(raw_section_id, int) and sections:
                    # Ajustar índice (1-based a 0-based)
                    idx = raw_section_id - 1
                    if 0 <= idx < len(sections):
                        real_section = sections[idx]
                        origen_data["section_id"] = real_section.id
                        # También podemos corregir la página si el LLM alucinó
                        if not origen_data.get("page") and real_section.page:
                            origen_data["page"] = real_section.page
                    else:
                        # Si el índice está fuera de rango, por defecto usar la primera del batch
                        # Esto previene errores si el LLM alucina un índice 99
                        origen_data["section_id"] = sections[0].id
                elif sections and ("section_id" not in origen_data or not origen_data["section_id"]):
                    # Si no viene section_id, asignar a la primera del batch por defecto
                    origen_data["section_id"] = sections[0].id

                origin = Origin.from_dict({
                    "document_id": document_id,
                    **origen_data,
                })

                # Construir Metadata
                metadata = QuestionMetadata.from_dict(
                    preg.get("sm2_metadata", preg.get("metadata", {}))
                )

                # Crear Question según tipo
                # Buscar contenido en 'contenido_tipo', 'content' o usar la raíz
                contenido = preg.get("contenido_tipo", preg.get("content", preg))

                if question_type == QuestionType.FLASHCARD:
                    question = Question.create_flashcard(
                        anverso=contenido.get("anverso", contenido.get("frente", contenido.get("front", preg.get("pregunta", "")))),
                        reverso=contenido.get("reverso", contenido.get("back", preg.get("respuesta", "")),),
                        origin=origin,
                        metadata=metadata,
                    )
                elif question_type == QuestionType.TRUE_FALSE:
                    question = Question.create_true_false(
                        pregunta=contenido.get("pregunta", contenido.get("afirmacion", contenido.get("question", contenido.get("statement", "")))),
                        respuesta_correcta=contenido.get("respuesta_correcta", contenido.get("respuesta", contenido.get("correct_answer", True))),
                        explicacion=contenido.get("explicacion", contenido.get("justificacion", contenido.get("explanation", ""))),
                        origin=origin,
                        metadata=metadata,
                    )
                elif question_type == QuestionType.MULTIPLE_CHOICE:
                    question = Question.create_multiple_choice(
                        pregunta=contenido.get("pregunta", contenido.get("question", preg.get("pregunta", ""))),
                        opciones=contenido.get("opciones", contenido.get("options", [])),
                        respuesta_correcta=contenido.get("respuesta_correcta", contenido.get("correct_answer", 0)),
                        origin=origin,
                        metadata=metadata,
                        explicacion=contenido.get("explicacion", contenido.get("explanation", "")),
                    )
                elif question_type == QuestionType.CLOZE:
                    question = Question.create_cloze(
                        texto_con_espacios=contenido.get("texto_con_espacios", contenido.get("text", "")),
                        respuestas_validas=contenido.get("respuestas_validas", contenido.get("answers", [])),
                        origin=origin,
                        metadata=metadata,
                    )
                else:
                    continue

                questions.append(question)

            except Exception as e:
                print(f"Error creating question {i+1}: {e}")
                continue

        print(f"Total questions created: {len(questions)}")
        return questions