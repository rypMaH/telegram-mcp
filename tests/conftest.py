"""Shared pytest setup for import-time Telegram configuration."""

import os

import pytest

from session_env_guard import neutralize_dotenv_accounts

# Must run before anything imports `telegram_mcp.runtime`, which calls
# `load_dotenv()` at import and would otherwise pick up the developer's
# labelled accounts from `.env` (see session_env_guard for why blanking works).
neutralize_dotenv_accounts()

os.environ.setdefault("TELEGRAM_API_ID", "12345")
os.environ.setdefault("TELEGRAM_API_HASH", "dummy_hash")
os.environ.setdefault("TELEGRAM_SESSION_NAME", "test_session")


@pytest.fixture
def transcript_cache_dir(tmp_path, monkeypatch):
    """Isolated, per-test SQLite transcript cache directory."""
    d = tmp_path / "transcripts"
    monkeypatch.setenv("TELEGRAM_TRANSCRIPT_CACHE_DIR", str(d))
    return d


@pytest.fixture(autouse=True)
def _clear_expected_username(monkeypatch):
    """Keep a developer's TELEGRAM_EXPECTED_USERNAME* (.env) away from fake clients."""
    for key in list(os.environ):
        if key.startswith("TELEGRAM_EXPECTED_USERNAME"):
            monkeypatch.delenv(key, raising=False)
