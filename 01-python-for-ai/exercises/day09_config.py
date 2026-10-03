"""Day 9 — Configuration & secrets: environment variables, .env files, pydantic-settings.

Run:  uv run pytest tests/test_day09_config.py -v
See it live first:  uv run python lessons/lesson6_config_secrets.py

Why this matters: on Days 11-14 you'll call a real LLM API. That needs an API key,
and a key must NEVER be written in your code or committed to git. The standard way:
keep it in an environment variable (or a `.env` file that git ignores) and read it
when the program starts.

This day does NOT depend on Days 1-8. Every exercise stands alone.
"""

import os
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class MissingConfigError(Exception):
    """Raised when a required setting is not set."""


# ---------------------------------------------------------------------------
# Exercise 1 — read one environment variable
# ---------------------------------------------------------------------------
def get_env(name: str, default: str | None = None) -> str:
    """Return the environment variable `name`.

    - set and not blank        -> return its value
    - not set, `default` given -> return `default`
    - not set, no default      -> raise MissingConfigError (message must contain `name`)

    A BLANK value ("" or only spaces) counts as NOT set. This catches the classic
    mistake of a .env line like  `API_KEY=`  with nothing after the "=".

    Hint: os.environ.get(name) returns None when the variable doesn't exist.
    """
    value = os.environ.get(name)
    if value is not None and value.strip():
        return value
    if default is not None:
        return default
    raise MissingConfigError(f"{name} is missing")


# ---------------------------------------------------------------------------
# Exercise 2 — never print a secret in full
# ---------------------------------------------------------------------------
def mask_secret(value: str) -> str:
    """Hide a secret for logging: keep only the LAST 4 characters visible.

        "abcdefghijkl" -> "********ijkl"      (same length, last 4 visible)

    Values with 8 or fewer characters are hidden completely: "short" -> "*****".
    An empty string stays "".

    Hint: "*" * 3 gives "***", and value[-4:] gives the last 4 characters.
    """
    if len(value)<=8:
        return "*"* len(value)
    return "*" * (len(value)-4)+value[-4:]


# ---------------------------------------------------------------------------
# Exercise 3 — one Settings class for the whole app
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    """All app configuration, read from environment variables and/or a .env file.

    TODO: add these four fields. Names are matched to environment variables
    case-insensitively, so the field `anthropic_api_key` reads ANTHROPIC_API_KEY.

      - anthropic_api_key: SecretStr    REQUIRED (no default)
      - llm_model: str                  default "claude-sonnet-5"
      - max_retries: int                default 3, allowed 0 to 10   (Field(ge=..., le=...))
      - timeout_seconds: float          default 30.0, must be > 0    (Field(gt=...))

    SecretStr is Pydantic's "password" type: printing the object shows '**********'
    instead of the real value. To get the real value you must ask on purpose:
    settings.anthropic_api_key.get_secret_value().

    Remember to import SecretStr and Field from pydantic.

    Order of priority when the same setting is given in several places:
        explicit argument  >  real environment variable  >  .env file  >  default
    """

    anthropic_api_key:SecretStr = os.environ.get("anthropic_api_key")
    llm_model:str = os.environ.get("llm_model","claude-sonnet-5")
    max_retries:int = os.environ.get("max_retries",Field(default=3,ge=0,le=11))
    timeout_seconds:float = os.environ.get("timeout_seconds",Field(default=30.0,ge=11))

    if  anthropic_api_key:
        raise MissingConfigError("anthropic_api_key is missing ")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# ---------------------------------------------------------------------------
# Exercise 4 — turn settings into HTTP headers
# ---------------------------------------------------------------------------
def build_headers(settings: Settings) -> dict[str, str]:
    """Return the headers the Anthropic API expects:

        {
            "x-api-key": <the REAL key>,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    Only reveal the secret here, at the moment you actually need it.
    Hint: .get_secret_value()
    """
    return { "x-api-key": settings.anthropic_api_key.get_secret_value(),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
