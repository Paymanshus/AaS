from app.core.config import Settings


def _settings(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)


def test_prefers_gemini_when_only_gemini_key_is_present() -> None:
    settings = _settings(GEMINI_API_KEY="g-key")
    assert settings.resolved_model_provider() == "gemini"
    assert settings.resolved_model_name() == settings.gemini_model


def test_falls_back_to_openai_when_gemini_key_is_missing() -> None:
    settings = _settings(OPENAI_API_KEY="o-key")
    assert settings.resolved_model_provider() == "openai"
    assert settings.resolved_model_name() == settings.openai_model


def test_model_provider_selects_openai_when_both_keys_present() -> None:
    settings = _settings(GEMINI_API_KEY="g-key", OPENAI_API_KEY="o-key", MODEL_PROVIDER="openai")
    assert settings.resolved_model_provider() == "openai"
    assert settings.resolved_model_name() == settings.openai_model


def test_model_provider_selects_gemini_when_both_keys_present() -> None:
    settings = _settings(GEMINI_API_KEY="g-key", OPENAI_API_KEY="o-key", MODEL_PROVIDER="gemini")
    assert settings.resolved_model_provider() == "gemini"
    assert settings.resolved_model_name() == settings.gemini_model


def test_invalid_model_provider_defaults_to_gemini_when_both_keys_present() -> None:
    settings = _settings(GEMINI_API_KEY="g-key", OPENAI_API_KEY="o-key", MODEL_PROVIDER="invalid")
    assert settings.resolved_model_provider() == "gemini"
    assert settings.resolved_model_name() == settings.gemini_model


def test_returns_none_when_no_provider_keys_are_set() -> None:
    settings = _settings()
    assert settings.resolved_model_provider() is None
    assert settings.resolved_model_name() is None
