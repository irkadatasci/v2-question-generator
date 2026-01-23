"""
Config Command - Comando para gestionar configuración.
"""

from pathlib import Path

from ....infrastructure.config import Settings, ConfigLoader


class ConfigCommand:
    """Comando para gestionar la configuración."""

    def __init__(self, settings: Settings):
        """
        Args:
            settings: Configuración de la aplicación
        """
        self._settings = settings

    def execute(self, action: str) -> int:
        """
        Ejecuta la acción de configuración.

        Args:
            action: Acción a realizar (show, init, providers)

        Returns:
            Código de salida
        """
        if action == "show":
            return self._show_config()
        elif action == "init":
            return self._init_config()
        elif action == "providers":
            return self._show_providers()
        else:
            print(f"Acción desconocida: {action}")
            return 1

    def _show_config(self) -> int:
        """Muestra la configuración actual."""
        print("=" * 60)
        print("⚙️  CONFIGURACIÓN ACTUAL")
        print("=" * 60)

        config = self._settings.to_dict()

        print(f"\n🤖 LLM:")
        print(f"   Proveedor por defecto: {config['default_llm_provider']}")
        print(f"   Proveedores configurados: {', '.join(config['configured_providers']) or 'ninguno'}")

        print(f"\n📁 Rutas:")
        print(f"   Prompts: {config['paths']['prompts']}")
        print(f"   Output: {config['paths']['output']}")

        print(f"\n🔍 Clasificación:")
        print(f"   Umbral relevante: {config['classification']['threshold_relevant']}")
        print(f"   Umbral revisión: {config['classification']['threshold_review']}")

        print(f"\n📝 Generación:")
        print(f"   Batch size: {config['generation']['batch_size']}")
        print(f"   Tipo por defecto: {config['generation']['question_type']}")

        print(f"\n🐛 Debug: {'Sí' if config['debug'] else 'No'}")

        # Validar configuración
        is_valid, errors = self._settings.validate()
        if not is_valid:
            print(f"\n⚠️  Problemas de configuración:")
            for error in errors:
                print(f"   - {error}")

        return 0

    def _init_config(self) -> int:
        """Crea archivo de configuración."""
        config_path = Path("config.json")

        if config_path.exists():
            print(f"⚠️  Ya existe {config_path}")
            print("   Use --config para especificar otra ruta")
            return 1

        ConfigLoader.create_template(config_path)
        print(f"✅ Archivo de configuración creado: {config_path}")
        print("\n📝 Pasos siguientes:")
        print("   1. Configure las API keys en variables de entorno:")
        print("      export MOONSHOT_API_KEY=tu_api_key")
        print("      export GROQ_API_KEY=tu_api_key")
        print("      export OPENAI_API_KEY=tu_api_key")
        print("   2. O añádalas a un archivo .env")
        print("   3. Ajuste los parámetros en config.json según necesite")

        return 0

    def _show_providers(self) -> int:
        """Muestra estado de proveedores de LLM."""
        print("=" * 60)
        print("🤖 PROVEEDORES DE LLM")
        print("=" * 60)

        providers = ["kimi", "groq", "openai", "ollama", "ollama_cloud"]

        for provider in providers:
            settings = self._settings.get_llm_settings(provider)
            status = "✅ Configurado" if settings.is_configured() else "❌ No configurado"

            print(f"\n{provider.upper()}:")
            print(f"   Estado: {status}")
            print(f"   Modelo: {settings.model or '(default)'}")

            if provider in ["ollama", "ollama_cloud"]:
                print(f"   URL: {settings.base_url or '(default)'}")

        configured = self._settings.get_configured_providers()
        print(f"\n📊 Resumen: {len(configured)}/{len(providers)} proveedores configurados")

        if not configured:
            print("\n💡 Para configurar un proveedor:")
            print("   export MOONSHOT_API_KEY=tu_api_key_de_kimi")
            print("   export GROQ_API_KEY=tu_api_key_de_groq")
            print("   export OPENAI_API_KEY=tu_api_key_de_openai")
            print("   export OLLAMA_CLOUD_API_KEY=tu_api_key_de_ollama_cloud")

        return 0
