"""Keep a developer's `.env` session labels out of the test suite.

`runtime.py` calls `load_dotenv()` at import, so a labelled account already in
the developer's `.env` (e.g. `TELEGRAM_SESSION_STRING_MCP`) becomes a second
entry in `runtime.clients`. Tests that assume one client then fail with
`Error: 'account' is required` or `JSONDecodeError`.

Deleting the variable does not work: `load_dotenv()` sees the key as absent and
re-adds it. A set-but-empty value is skipped by `load_dotenv()` (it never
overwrites an existing key) and by `_discover_accounts()` (which ignores falsy
values), so blanking is what actually isolates the suite.
"""

import os

from dotenv import dotenv_values

# Labelled account spellings: TELEGRAM_SESSION_STRING_<LABEL> / _NAME_<LABEL>.
_SUFFIXED_PREFIXES = ("TELEGRAM_SESSION_STRING_", "TELEGRAM_SESSION_NAME_")
# A session pool also creates an extra client for the default account.
_POOL_VAR = "TELEGRAM_SESSION_STRINGS"


def neutralize_dotenv_accounts(env=None, dotenv=None):
    """Blank labelled `.env` sessions so the suite sees a single account.

    Returns the names of the variables that were blanked.
    """
    env = os.environ if env is None else env
    values = dotenv_values() if dotenv is None else dotenv

    blanked = []
    for key in values:
        if key == _POOL_VAR or key.startswith(_SUFFIXED_PREFIXES):
            env[key] = ""
            blanked.append(key)
    return blanked
