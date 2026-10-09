import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_SECRET_KEY, Settings


def test_production_refuses_default_secret_key():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(environment="production", secret_key=DEFAULT_SECRET_KEY)


def test_production_refuses_default_webhook_secret():
    with pytest.raises(ValidationError, match="PAYMENT_WEBHOOK_SECRET"):
        Settings(environment="production", secret_key="x" * 40)


def test_production_accepts_strong_secrets():
    cfg = Settings(
        environment="production", secret_key="x" * 40, payment_webhook_secret="segredo-forte"
    )
    assert cfg.environment == "production"


def test_development_defaults_are_usable():
    cfg = Settings(environment="development")
    assert cfg.access_token_expire_minutes <= 30
    assert cfg.payment_gateway == "fake"
