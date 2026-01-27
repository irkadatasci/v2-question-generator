"""
LMStudio Backend - Implementación para LMStudio (OpenAI compatible).
"""

from typing import List

from .openai import OpenAIBackend


class LMStudioBackend(OpenAIBackend):
    """
    Backend para LMStudio.
    
    LMStudio expone una API compatible con OpenAI corriendo localmente.
    Por defecto corre en http://localhost:1234/v1
    """

    DEFAULT_MODEL = "local-model"
    DEFAULT_BASE_URL = "http://localhost:1234/v1"

    @property
    def provider_name(self) -> str:
        return "lmstudio"

    def _initialize_client(self) -> None:
        """Inicializa el cliente compatible con OpenAI apuntando a local."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Se requiere openai>=1.0.0: pip install openai")

        # LMStudio no requiere API key real, pero el cliente sí espera un valor
        api_key = self._config.api_key or "lm-studio"
        base_url = self._config.base_url or self.DEFAULT_BASE_URL

        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self._config.timeout,
        )

    def _call_api(
        self,
        prompt: str,
        system_prompt: str,
        response_format: str,
    ):
        """
        Realiza la llamada a la API. 
        Forzamos response_format a None para evitar errores 400 en servidores locales
        que no soportan json_object, confiando en nuestro parser robusto.
        """
        return super()._call_api(prompt, system_prompt, response_format=None)

    def estimate_cost(self, tokens_prompt: int, tokens_completion: int) -> float:
        """Costo cero para ejecución local."""
        return 0.0

    def get_available_models(self) -> List[str]:
        """
        Intenta obtener los modelos cargados en LMStudio.
        Si falla, retorna el modelo por defecto.
        """
        try:
            if self._client is None:
                self._initialize_client()
            
            models = self._client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return [self.DEFAULT_MODEL]
