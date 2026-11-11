# Repository Guidelines

## Architecture

- `main.py` is a thin compatibility shim: it re-exports `telegram_mcp.runtime`, `telegram_mcp.runner` and `telegram_mcp.tools`, and keeps `main.SERVER_ALLOWED_ROOTS` / `main.ALLOWED_CHAT_IDS` monkeypatchable by syncing them back into `runtime` before each guarded call. Real logic lives in the package.
- `telegram_mcp/runtime.py` (~2.8k lines) owns the FastMCP instance (`mcp`), env loading, client construction and account routing, the chat allowlist, file-path guards, error formatting, and the `with_account(readonly=...)` / `validate_id(...)` decorators. `telegram_mcp/runner.py` owns startup: session locks, transport selection, and `TELEGRAM_EXPOSED_TOOLS` pruning. `telegram_mcp/server.py` is an optional high-level facade (`get_server`, `get_http_app`, `serve`) over the same objects.
- Tool modules live in `telegram_mcp/tools/` and start with `from telegram_mcp.runtime import *` (runtime computes `__all__` at the bottom of the file). A tool declaration is `@mcp.tool(annotations=ToolAnnotations(...))` + `@with_account(readonly=...)` + optional `@validate_id("chat_id")`.
- To add a tool, define it in the matching module with that decorator stack; `@mcp.tool` registers it, and `telegram_mcp/tools/__init__.py` star-imports each module so registration happens on import. Adding the name to the module's `__all__` is what re-exports it as `main.<tool>` for tests and callers. Currently 150 tools are registered but 7 are *not* exported: `delete_forum_topic`, `edit_forum_topic`, `forward_messages`, `get_send_as`, `prepare_upload`, `remove_user`, `transcribe_voice`. `tools/stickers.py` is only a compatibility alias for `tools/custom_emoji.py`, not a real tool module (and is not imported by `tools/__init__.py`).
- `sanitize.py` is a top-level module (not in the package), imported as `import sanitize`. All Telegram user content returned to clients must go through it.
- Transports live in `telegram_mcp/transport/` (stdio, Streamable HTTP, legacy SSE). Importing `runtime` or `transport` calls `install_protocol_compatibility()`, which patches the MCP SDK to accept protocol `2026-07-28`; protocol code must go through that hook rather than raw SDK settings.

## Commands

- `uv sync` — install project plus the `dev` dependency group.
- `uv run main.py` — start the server. Needs `.env`; `sys.exit(1)` fires at import time if `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` are missing, so ad-hoc scripts must set them first.
- `uv run pytest` — full suite (1755 collected, 1744 passed / 11 skipped, ~19s). No env prefix needed.
- `uv run black --check .` — passes on a clean checkout (verified: 128 files unchanged) and is a gating CI job.
- `uv run flake8 .` — **fails with exactly 75 pre-existing violations** (60 × C901 complexity, 14 × E501, 1 × F841), so do not treat it as a regression you caused and do not "fix" them. The CI gate is only `flake8 . --select=E9,F63,F7,F82`, which passes; run that to check your own change, and keep new code under `max-complexity = 10` / 99 cols anyway.
- `uv run pre-commit install --hook-type pre-commit --hook-type pre-push` — hooks rewrite files (black, trailing-whitespace, end-of-file-fixer), so treat `pre-commit run --all-files` as a fixer, not a check. Pre-commit additionally runs `docker compose --env-file .env.example config` plus hadolint; pre-push runs the full coverage suite and `docker build`.
- `docker build --file Dockerfile --tag telegram-mcp:ci .` — the image installs from `requirements.txt`, so update that file alongside `pyproject.toml` when adding a dependency.

## Conventions enforced by tests

- Every optional argument that defaults to `None` must accept `null` in the JSON schema — annotate as `Optional[str] = None`, not `str = None`. `tests/test_tool_schema_null_defaults.py` walks every registered tool.
- Every registered tool carries `ToolAnnotations` with a `title` (verified: all 150). `readOnlyHint` is functional, not cosmetic: `TELEGRAM_EXPOSED_TOOLS=read-only` builds its tool set from it, so any tool that writes, sends, or creates a link must not claim `readOnlyHint=True` (`tests/test_side_effect_annotations.py`).
- Tool results are annotated as `audience=["user"]` by a hook in `runtime.py`; do not add per-tool audience annotations.

## Testing

- `tests/conftest.py` injects dummy `TELEGRAM_API_ID/HASH/SESSION_NAME` via `setdefault` and strips developer `TELEGRAM_EXPECTED_USERNAME*` values, so no live Telegram account is needed. Mock Telethon with `AsyncMock`.
- **Your local `.env` no longer leaks into the suite** — `tests/conftest.py` neutralises it. `runtime.py` calls `load_dotenv()` at import, so a labelled session in `.env` (e.g. `TELEGRAM_SESSION_STRING_MCP`) used to become a second entry in `runtime.clients`, failing hundreds of tests with `Error: 'account' is required. Available accounts: ...` or `json.decoder.JSONDecodeError`. `tests/session_env_guard.py` now blanks every labelled session (`TELEGRAM_SESSION_STRING_<LABEL>`, `TELEGRAM_SESSION_NAME_<LABEL>`, and the `TELEGRAM_SESSION_STRINGS` pool) before any import. Run a plain `uv run pytest`; no env prefix is needed. If you see that failure again, the guard is not running — check `conftest.py` imports it before `telegram_mcp.runtime`.
  - Blanking works because `load_dotenv()` never overwrites an existing key and `_discover_accounts()` skips falsy values. `env -u …` and `uv run --env-file .env.example` do **not** work — dotenv re-adds the label.
  - The guard deliberately leaves unsuffixed `TELEGRAM_SESSION_NAME`/`TELEGRAM_SESSION_STRING` alone: blanking those makes `_discover_accounts()` exit 1.
- Async tests need explicit `@pytest.mark.asyncio` (pytest-asyncio strict mode plus `--strict-markers` / `--strict-config`).
- The 80% coverage gate only measures `main`, `sanitize`, and `telegram_mcp.runtime` (see `[tool.coverage.run]`); tool modules are excluded by design, so shifting logic into a new `tools/*.py` will not help coverage.

## Gotchas

- Version `2.0.1` is hardcoded in four places: `pyproject.toml`, `manifest.json`, the HTTP discovery payload in `telegram_mcp/transport/http.py`, and `tests/test_protocol_negotiation.py`. Bump them together.
- Python versions differ by target: CI runs 3.11, `.python-version` and the Dockerfile pin 3.13, and `requires-python` is `>=3.10`. Keep code valid on all three.
- `main.py` and `runner.py` call `assert_safe_distribution()` before anything else. The `telegram-mcp` name on PyPI belongs to an unrelated project, so an installed distribution without source-checkout or git/file provenance aborts at startup; run from a clone or an explicit `git+https://` install.
- Startup acquires a per-session OS file lock (`telegram_mcp/singleton.py`). A second process using the same session exits instead of reconnecting; `TELEGRAM_SESSION_LOCK=shared` allows co-tenant instances on one host.
- `.env.example` is the authoritative list of most environment toggles (exposed tools, proxy, transcription, session locks), all read at import/startup — tests flip them with `monkeypatch.setenv`, so changing a default means editing `runtime.py`/`runner.py`, not just the docs. Two exceptions are documented only in the README: `TELEGRAM_ALLOWED_CHAT_IDS` (chat allowlist) and `TELEGRAM_ALLOWED_ROOTS` (file-path roots).
- `.codex/` holds local Codex/telegram credentials (`telegram-auth.json`, `telegram-headers.ps1`) plus a private gateway URL in `config.toml`. The whole directory is gitignored — keep it that way and never commit any of it.

## Commits and Pull Requests

Use a focused branch and short imperative subjects in `type(scope): summary` form, for example `fix(emoji): ensure parent directory exists when saving custom emoji preview`. Keep PR descriptions concise, link related issues, and report the checks you ran. Add or update tests when behavior changes.

## Configuration and Secrets

Keep `.env`, Telegram session strings, and `*.session` files out of commits. Use placeholders in examples and test fixtures. Message-deletion tools append metadata-only JSONL to `telegram_audit.log` (`TELEGRAM_AUDIT_LOG` overrides the path), and runtime logs go to `mcp_errors.log` — both are local state, never commit them.
