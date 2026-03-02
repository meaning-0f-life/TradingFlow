from typing import Dict, Any, Optional
import openai
from anthropic import Anthropic
from .base import BaseNode
from app.core.config import settings
from app.services.encryption import EncryptionService

class LLMNode(BaseNode):
    """Node for calling LLM APIs"""

    display_name = "LLM Call"
    description = "Call an LLM model (OpenAI, Anthropic, OpenRouter, DeepSeek, etc.)"
    category = "ai"

    # Supported providers
    PROVIDERS = {
        "openai": {
            "models": ["gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-3.5-turbo"],
            "default_model": "gpt-4",
            "base_url": "https://api.openai.com/v1"
        },
        "anthropic": {
            "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "default_model": "claude-3-sonnet-20240229",
            "base_url": None  # Anthropic uses its own client
        },
        "openrouter": {
            "models": [
                "openai/gpt-4o",
                "openai/gpt-4-turbo",
                "anthropic/claude-3-opus",
                "anthropic/claude-3-sonnet",
                "meta-llama/llama-3-70b-instruct",
                "google/gemini-pro",
                "google/gemini-3.1-pro-preview",
                "anthropic/claude-sonnet-4.6",
                "qwen/qwen3.5-397b-a17b",
                "minimax/minimax-m2.5",
                "z-ai/glm-5",
                "anthropic/claude-opus-4.6",
                "google/gemini-3-flash-preview",
                "arcee-ai/trinity-large-preview:free",
                "qwen/qwen3-235b-a22b-thinking-2507"
            ],
            "default_model": "google/gemini-3-flash-preview",
            "base_url": "https://openrouter.ai/api/v1"
        },
        "deepseek": {
            "models": ["deepseek-chat", "deepseek-coder"],
            "default_model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1"
        }
    }

    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", self.PROVIDERS.get(self.provider, {}).get("default_model", "gpt-4"))
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)
        self.system_prompt = config.get("system_prompt", "")
        self.user_prompt_template = config.get("user_prompt", "")

        # Validate provider
        if self.provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {self.provider}. Supported: {list(self.PROVIDERS.keys())}")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM call"""
        self._validate_config(["user_prompt"])

        # Get API key from context or database
        api_key = await self._get_api_key(context.get("db"), self.provider)

        # Prepare prompt with input substitution
        prompt = self._prepare_prompt(inputs)

        # Call LLM based on provider
        if self.provider == "openai":
            result = await self._call_openai_compatible(api_key, prompt)
        elif self.provider == "anthropic":
            result = await self._call_anthropic(api_key, prompt)
        elif self.provider in ["openrouter", "deepseek"]:
            result = await self._call_openai_compatible(
                api_key,
                prompt,
                custom_base_url=self.PROVIDERS[self.provider]["base_url"],
                is_openrouter=(self.provider == "openrouter")
            )
        else:
            raise ValueError(f"Provider {self.provider} not implemented")

        return result

    def _prepare_prompt(self, inputs: Dict[str, Any]) -> str:
        """Prepare user prompt by substituting input variables"""
        prompt = self.user_prompt_template

        # Replace {{input.port_name}} with actual values
        for port_name, value in inputs.items():
            placeholder = f"{{{{input.{port_name}}}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt

    async def _call_openai_compatible(
        self,
        api_key: str,
        prompt: str,
        custom_base_url: Optional[str] = None,
        is_openrouter: bool = False
    ) -> Dict[str, Any]:
        """Call OpenAI-compatible API (OpenAI, OpenRouter, DeepSeek)"""
        base_url = custom_base_url or self.PROVIDERS["openai"]["base_url"]

        # Prepare headers
        headers = {}
        app_url = getattr(settings, 'APP_URL', None)
        app_name = getattr(settings, 'APP_NAME', None)
        
        if app_url:
            headers["HTTP-Referer"] = app_url
        if app_name:
            headers["X-Title"] = app_name

        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=headers if headers else None
        )

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return {
            "response": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    async def _call_anthropic(self, api_key: str, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API"""
        client = Anthropic(api_key=api_key)

        messages = [{"role": "user", "content": prompt}]

        response = await client.messages.create(
            model=self.model,
            messages=messages,
            system=self.system_prompt if self.system_prompt else None,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return {
            "response": response.content[0].text,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }

    async def _get_api_key(self, db, service: str) -> str:
        """Get encrypted API key from database and decrypt it"""
        from sqlalchemy.orm import Session
        from app.models.api_key import APIKey
        from app.services.encryption import EncryptionService

        if not db:
            raise ValueError("Database session required to fetch API key")

        # For now, get the first active key for this service
        # In production, you'd get the key for the current user
        api_key_record = db.query(APIKey).filter(
            APIKey.service == service,
            APIKey.is_active == True
        ).first()

        if not api_key_record:
            raise ValueError(f"No API key found for service: {service}. Please add one in settings.")

        encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
        return encryption_service.decrypt(api_key_record.encrypted_key)

    @classmethod
    def get_ui_schema(cls) -> Dict[str, Any]:
        """Return UI schema for LLM node configuration"""
        # Build provider options
        provider_options = []
        model_options = []

        for provider, info in cls.PROVIDERS.items():
            provider_options.append({"value": provider, "label": provider.title()})
            for model in info["models"]:
                model_options.append({"value": model, "label": model, "provider": provider})

        return {
            "parameters": [
                {
                    "name": "provider",
                    "type": "select",
                    "title": "Provider",
                    "default": "openai",
                    "options": provider_options,
                    "description": "LLM provider to use"
                },
                {
                    "name": "model",
                    "type": "select",
                    "title": "Model",
                    "default": "gpt-4",
                    "options": model_options,
                    "description": "Model to use"
                },
                {
                    "name": "temperature",
                    "type": "number",
                    "title": "Temperature",
                    "default": 0.7,
                    "minimum": 0,
                    "maximum": 2,
                    "step": 0.1,
                    "description": "Controls randomness (0 = deterministic, 2 = very random)"
                },
                {
                    "name": "max_tokens",
                    "type": "number",
                    "title": "Max Tokens",
                    "default": 1000,
                    "minimum": 1,
                    "maximum": 4000,
                    "description": "Maximum tokens in response"
                },
                {
                    "name": "system_prompt",
                    "type": "textarea",
                    "title": "System Prompt",
                    "default": "",
                    "description": "System prompt to set context"
                },
                {
                    "name": "user_prompt",
                    "type": "textarea",
                    "title": "User Prompt",
                    "default": "",
                    "description": "User prompt. Use {{input.port_name}} to insert data from connected nodes"
                }
            ],
            "outputs": [
                {"name": "response", "type": "string", "description": "LLM response text"},
                {"name": "usage", "type": "object", "description": "Token usage statistics"}
            ]
        }