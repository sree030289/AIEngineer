"""Lesson 6 — Environment variables, .env files and secrets. Plain Python, no async.

Run:  uv run python lessons/lesson6_config_secrets.py
"""

import os
import tempfile
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def step(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


# ---------------------------------------------------------------------------
step("1. An environment variable is a named piece of text that lives OUTSIDE your code")
# ---------------------------------------------------------------------------
os.environ["DEMO_COLOR"] = "blue"                 # normally set by your shell / .env, not in code
print("os.environ['DEMO_COLOR']        ->", os.environ["DEMO_COLOR"])
print("os.environ.get('NOPE')          ->", os.environ.get("NOPE"), "   (None when missing, no crash)")
print("os.environ.get('NOPE', 'dflt')  ->", os.environ.get("NOPE", "dflt"))
try:
    os.environ["NOPE"]
except KeyError as e:
    print("os.environ['NOPE']              -> KeyError", e, "   (square brackets crash when missing)")
print("\nAlways a STRING:", repr(os.environ["DEMO_COLOR"]), "- numbers arrive as text too.")

# ---------------------------------------------------------------------------
step("2. Why not just write the key in the code?")
# ---------------------------------------------------------------------------
print("""   API_KEY = "sk-ant-abc123"      <- NO. It goes into git, then onto GitHub, then into
                                     the hands of bots that scan GitHub for keys, in minutes.

   Instead:  the key lives in the environment (or a .env file listed in .gitignore),
             and the code only says WHICH variable to read.""")


# ---------------------------------------------------------------------------
step("3. A Settings class: read, convert and VALIDATE all config in one place")
# ---------------------------------------------------------------------------
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: SecretStr                        # required: no default
    llm_model: str = "claude-sonnet-5"                  # optional: has a default
    max_retries: int = Field(default=3, ge=0, le=10)    # text "5" becomes the number 5, and is range-checked


os.environ["ANTHROPIC_API_KEY"] = "sk-ant-demo-1234567890"
os.environ["MAX_RETRIES"] = "5"
settings = Settings(_env_file=None)
print("max_retries =", settings.max_retries, type(settings.max_retries).__name__, " (converted from text)")
print("llm_model   =", settings.llm_model, " (default, because LLM_MODEL isn't set)")

# ---------------------------------------------------------------------------
step("4. SecretStr: printing the object does NOT leak the key")
# ---------------------------------------------------------------------------
print("print(settings)  ->", settings)
print("real value only on purpose ->", settings.anthropic_api_key.get_secret_value())

# ---------------------------------------------------------------------------
step("5. Bad config fails at STARTUP, with a clear message")
# ---------------------------------------------------------------------------
os.environ["MAX_RETRIES"] = "99"
try:
    Settings(_env_file=None)
except Exception as e:
    print(str(e).splitlines()[0])
    print(str(e).splitlines()[1], "->", str(e).splitlines()[2].strip())
os.environ["MAX_RETRIES"] = "5"

# ---------------------------------------------------------------------------
step("6. A .env file, and who wins when the same setting appears twice")
# ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as folder:
    env_file = Path(folder) / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=from-the-file\nLLM_MODEL=claude-haiku-4-5\n")

    os.environ.pop("ANTHROPIC_API_KEY")
    from_file = Settings(_env_file=env_file)
    print("only the file has the key   ->", from_file.anthropic_api_key.get_secret_value())

    os.environ["ANTHROPIC_API_KEY"] = "from-real-env"
    both = Settings(_env_file=env_file)
    print("env var AND file both set   ->", both.anthropic_api_key.get_secret_value(), "(real env var wins)")
    print("LLM_MODEL only in the file  ->", both.llm_model)
    explicit = Settings(_env_file=env_file, anthropic_api_key="from-argument")
    print("argument passed in code     ->", explicit.anthropic_api_key.get_secret_value(), "(argument wins over everything)")

print("\nPriority:  argument  >  real env var  >  .env file  >  default value")
