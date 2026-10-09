"""Configuração central da aplicação, lida de variáveis de ambiente / arquivo .env."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "dev-secret-troque-em-producao-0123456789abcdef"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    app_name: str = "Semeando"

    database_url: str = "postgresql+psycopg://semeando:semeando@localhost:5433/semeando"

    # Autenticação
    secret_key: str = DEFAULT_SECRET_KEY
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_cookie_name: str = "semeando_refresh"
    refresh_cookie_secure: bool = False

    # HTTP
    cors_origins: list[str] = [
        "http://localhost:5173",  # painel administrativo
        "http://localhost:5174",  # portal do responsável
        "http://localhost:5175",  # portal do aluno
        "http://localhost:5176",  # portal do professor
        "http://localhost:8080",
    ]

    # Rate limit (requisições por janela de 60 segundos)
    login_rate_limit_per_minute: int = 5
    register_rate_limit_per_minute: int = 3
    assistente_rate_limit_per_minute: int = 10

    # Uploads de documentos da matrícula
    upload_dir: str = "uploads"
    upload_max_bytes: int = 5 * 1024 * 1024

    # Financeiro
    payment_gateway: Literal["fake", "cora"] = "fake"
    payment_webhook_secret: str = "dev-webhook-secret"  # noqa: S105
    dia_vencimento_mensalidade: int = 10
    dias_vencimento_matricula: int = 5
    inadimplencia_dias_tolerancia: int = 5
    inadimplencia_bloqueia: list[str] = ["REMATRICULA", "SERVICOS_EXTRAS"]

    # Assistente de IA (DeepSeek, API compatível com OpenAI).
    # Chave de TESTE hardcoded de propósito (projeto acadêmico); a variável de ambiente
    # DEEPSEEK_API_KEY sobrescreve. Troque/revogue a chave se o repositório for público.
    deepseek_api_key: str = "COLE_AQUI_A_API_KEY_DE_TESTE_DA_DEEPSEEK"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: float = 45.0
    assistente_historico_max_mensagens: int = 20
    assistente_max_passos: int = 5
    assistente_acao_expira_minutos: int = 10

    @model_validator(mode="after")
    def _check_production_secrets(self) -> Self:
        if self.environment == "production":
            if self.secret_key == DEFAULT_SECRET_KEY or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY precisa ser definida (mín. 32 caracteres) em produção")
            if self.payment_webhook_secret == "dev-webhook-secret":  # noqa: S105
                raise ValueError("PAYMENT_WEBHOOK_SECRET precisa ser definida em produção")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
