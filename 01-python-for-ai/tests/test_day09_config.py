import os

import pytest
from pydantic import ValidationError

from exercises.day09_config import MissingConfigError, Settings, build_headers, get_env, mask_secret

SETTING_VARS = ["ANTHROPIC_API_KEY", "LLM_MODEL", "MAX_RETRIES", "TIMEOUT_SECONDS"]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Runs before EVERY test: remove our settings from the environment so a real
    key on your machine can't change the results. monkeypatch restores everything
    automatically when each test ends."""
    for name in SETTING_VARS + ["MY_TEST_VAR"]:
        monkeypatch.delenv(name, raising=False)


# --- Exercise 1: get_env -----------------------------------------------------
def test_get_env_returns_value(monkeypatch):
    monkeypatch.setenv("MY_TEST_VAR", "hello")
    assert get_env("MY_TEST_VAR") == "hello"


def test_get_env_uses_default_when_missing():
    assert get_env("MY_TEST_VAR", "fallback") == "fallback"


def test_get_env_missing_without_default_raises_with_name():
    with pytest.raises(MissingConfigError) as exc:
        get_env("MY_TEST_VAR")
    assert "MY_TEST_VAR" in str(exc.value)


@pytest.mark.parametrize("blank", ["", "   "])
def test_get_env_blank_counts_as_missing(monkeypatch, blank):
    monkeypatch.setenv("MY_TEST_VAR", blank)
    with pytest.raises(MissingConfigError):
        get_env("MY_TEST_VAR")
    assert get_env("MY_TEST_VAR", "fallback") == "fallback"


def test_get_env_value_wins_over_default(monkeypatch):
    monkeypatch.setenv("MY_TEST_VAR", "real")
    assert get_env("MY_TEST_VAR", "fallback") == "real"


# --- Exercise 2: mask_secret -------------------------------------------------
def test_mask_keeps_last_four():
    assert mask_secret("abcdefghijkl") == "********ijkl"


def test_mask_realistic_key_never_contains_the_secret_part():
    key = "sk-ant-api03-SECRETPART-1234"
    masked = mask_secret(key)
    assert masked.endswith("1234")
    assert len(masked) == len(key)
    assert "SECRETPART" not in masked


@pytest.mark.parametrize("short", ["short", "12345678", "a"])
def test_mask_short_values_fully_hidden(short):
    assert mask_secret(short) == "*" * len(short)


def test_mask_empty_string():
    assert mask_secret("") == ""


def test_mask_nine_characters_is_the_boundary():
    assert mask_secret("123456789") == "*****6789"


# --- Exercise 3: Settings ----------------------------------------------------
def test_settings_reads_required_key_and_defaults(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-1234")
    s = Settings(_env_file=None)
    assert s.anthropic_api_key.get_secret_value() == "sk-test-1234"
    assert s.llm_model == "claude-sonnet-5"
    assert s.max_retries == 3
    assert s.timeout_seconds == 30.0


def test_settings_env_vars_override_defaults(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-1234")
    monkeypatch.setenv("LLM_MODEL", "claude-haiku-4-5")
    monkeypatch.setenv("MAX_RETRIES", "5")           # env vars are always text...
    monkeypatch.setenv("TIMEOUT_SECONDS", "12.5")
    s = Settings(_env_file=None)
    assert s.llm_model == "claude-haiku-4-5"
    assert s.max_retries == 5                         # ...Pydantic converts them
    assert s.timeout_seconds == 12.5


def test_settings_missing_key_is_an_error():
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)
    assert "anthropic_api_key" in str(exc.value)


@pytest.mark.parametrize("name, bad_value", [("MAX_RETRIES", "99"), ("MAX_RETRIES", "-1"),
                                             ("TIMEOUT_SECONDS", "0"), ("MAX_RETRIES", "lots")])
def test_settings_rejects_bad_values(monkeypatch, name, bad_value):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-1234")
    monkeypatch.setenv(name, bad_value)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_hides_the_secret_when_printed(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-super-secret-value")
    s = Settings(_env_file=None)
    assert "sk-super-secret-value" not in repr(s)
    assert "sk-super-secret-value" not in str(s)


def test_settings_reads_dotenv_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=sk-from-file\nLLM_MODEL=claude-opus-5-5\nUNRELATED=ignored\n")
    s = Settings(_env_file=env_file)
    assert s.anthropic_api_key.get_secret_value() == "sk-from-file"
    assert s.llm_model == "claude-opus-5-5"


def test_real_env_var_beats_dotenv_file(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=from-file\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-real-env")
    assert Settings(_env_file=env_file).anthropic_api_key.get_secret_value() == "from-real-env"


def test_explicit_argument_beats_everything(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-env")
    s = Settings(_env_file=None, anthropic_api_key="from-argument")
    assert s.anthropic_api_key.get_secret_value() == "from-argument"


# --- Exercise 4: build_headers -----------------------------------------------
def test_build_headers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-1234")
    assert build_headers(Settings(_env_file=None)) == {
        "x-api-key": "sk-test-1234",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def test_environment_is_restored_after_each_test():
    # monkeypatch undid the previous tests' setenv calls.
    assert "MY_TEST_VAR" not in os.environ
