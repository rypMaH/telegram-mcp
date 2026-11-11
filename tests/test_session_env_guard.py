"""Tests for the `.env` session isolation guard."""

import os

from session_env_guard import neutralize_dotenv_accounts


def test_blanks_labelled_session_strings():
    env = {"TELEGRAM_SESSION_STRING_MCP": "leaked", "KEEP": "1"}
    blanked = neutralize_dotenv_accounts(
        env=env,
        dotenv={"TELEGRAM_SESSION_STRING_MCP": "leaked", "TELEGRAM_SESSION_NAME": "x"},
    )

    assert env["TELEGRAM_SESSION_STRING_MCP"] == ""
    assert env["KEEP"] == "1"
    assert blanked == ["TELEGRAM_SESSION_STRING_MCP"]


def test_blanks_labelled_session_names_and_pool():
    env = {}
    dotenv = {
        "TELEGRAM_SESSION_NAME_WORK": "work.session",
        "TELEGRAM_SESSION_STRINGS": "s1 s2",
        "TELEGRAM_API_ID": "12345",
    }

    blanked = neutralize_dotenv_accounts(env=env, dotenv=dotenv)

    assert env["TELEGRAM_SESSION_NAME_WORK"] == ""
    assert env["TELEGRAM_SESSION_STRINGS"] == ""
    assert sorted(blanked) == ["TELEGRAM_SESSION_NAME_WORK", "TELEGRAM_SESSION_STRINGS"]


def test_leaves_unsuffixed_session_name_alone():
    """An unsuffixed name is the fallback account; blanking it exits the server."""
    env = {}
    dotenv = {"TELEGRAM_SESSION_NAME": "test_session"}

    blanked = neutralize_dotenv_accounts(env=env, dotenv=dotenv)

    assert "TELEGRAM_SESSION_NAME" not in env
    assert blanked == []


def test_blanked_value_survives_load_dotenv(tmp_path, monkeypatch):
    """The whole point: load_dotenv must not restore a blanked label."""
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("TELEGRAM_SESSION_STRING_MCP=realsecret\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_SESSION_STRING_MCP", raising=False)

    env = {"TELEGRAM_SESSION_STRING_MCP": ""}
    neutralize_dotenv_accounts(env=env, dotenv={"TELEGRAM_SESSION_STRING_MCP": "realsecret"})

    from dotenv import load_dotenv

    monkeypatch.setenv("TELEGRAM_SESSION_STRING_MCP", "")
    load_dotenv(dotenv_file, override=False)

    assert os.environ["TELEGRAM_SESSION_STRING_MCP"] == ""
