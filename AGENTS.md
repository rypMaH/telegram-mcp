# Repository Guidelines

## Project Structure

- `main.py` is the compatibility entry point. `telegram_mcp/runtime.py` handles shared configuration, account routing, and access checks. `telegram_mcp/runner.py` handles startup.
- Add MCP tools to the relevant module in `telegram_mcp/tools/`, such as `chats.py` or `messages.py`. The stdio and Streamable HTTP implementations live in `telegram_mcp/transport/`.
- Tests live in `tests/`. `examples/docker/` contains deployment examples, `skills/` contains usage workflows, and `screenshots/` contains README images.

## Build and Development

- `uv sync` installs the project and development dependencies from the checkout. CI uses Python 3.11.
- `uv run main.py` starts the MCP server. Copy `.env.example` to `.env` and configure your Telegram credentials and session before starting it.
- `docker build --file Dockerfile --tag telegram-mcp:ci .` builds the image checked by the pre-push hook.
- `uv run pre-commit install --hook-type pre-commit --hook-type pre-push` installs the repository hooks.

## Coding Style

Use four-space indentation, `snake_case` for Python modules and functions, and `PascalCase` for classes. Black and Flake8 use a 99-character line length. Run `uv run black --check .` and `uv run flake8 .` before opening a pull request.

## Testing

Put behavior tests in `tests/test_*.py` and name test functions `test_*`. Use pytest, mark async tests with `@pytest.mark.asyncio`, and mock Telethon calls with `AsyncMock` so tests can run without a live account. Run `uv run pytest` for the full suite or `uv run pytest tests/test_resolve_username.py` for a focused check. CI runs `uv run pytest --cov --cov-report=term-missing --cov-report=xml` and requires at least 80% branch-enabled coverage across `main`, `sanitize`, and `telegram_mcp.runtime`.

## Commits and Pull Requests

Use a focused branch and short, imperative commit subjects. Recent commits generally use `type(scope): summary` with optional scope, for example `fix(emoji): ensure parent directory exists when saving custom emoji preview`. Keep the PR description concise, link related issues when available, and report the checks you ran. Add or update tests when behavior changes.

## Configuration and Secrets

Keep `.env`, Telegram session strings, and `*.session` files out of commits. Use placeholders in examples and test fixtures.
