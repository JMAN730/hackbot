"""Tests for HackBot CLI command handling."""

from hackbot.cli import HackBotApp
from hackbot.config import HackBotConfig


def test_key_deepseek_prefix_switches_provider_before_validation(monkeypatch):
    saved = {}

    def fake_validate(self):
        saved["provider_at_validation"] = self.config.provider
        saved["model_at_validation"] = self.config.model
        saved["api_key_at_validation"] = self.config.api_key
        return {"valid": True, "message": "ok"}

    monkeypatch.setattr("hackbot.cli.save_config", lambda cfg: saved.setdefault("saved", cfg))
    monkeypatch.setattr("hackbot.core.engine.AIEngine.validate_api_key", fake_validate)

    app = HackBotApp(HackBotConfig())

    assert app._set_key("deepseek sk-deepseek-test") is True
    assert app.config.ai.provider == "deepseek"
    assert app.config.ai.model == "deepseek-chat"
    assert app.config.ai.api_key == "sk-deepseek-test"
    assert saved["provider_at_validation"] == "deepseek"
    assert saved["model_at_validation"] == "deepseek-chat"
    assert saved["api_key_at_validation"] == "sk-deepseek-test"


def test_key_deep_alias_requires_key_and_does_not_save(monkeypatch):
    saved = {"called": False}
    monkeypatch.setattr("hackbot.cli.save_config", lambda cfg: saved.update(called=True))

    app = HackBotApp(HackBotConfig())

    assert app._set_key("deep") is True
    assert app.config.ai.provider == "openai"
    assert app.config.ai.api_key == ""
    assert saved["called"] is False
