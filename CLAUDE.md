# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A website advertising Aikido classes taught by Jeremy Nelson in Bayfield, Colorado (at Elevated Martial Arts). The site is built as a single static `index.html` that loads [PyScript](https://pyscript.net/) (currently `2026.3.1`), allowing Python to run in the browser. `main.py` is the uv-generated package entry point and is currently a placeholder.

The page is mostly static content. PyScript drives one feature: "Sign in with ORCID" (see below).

## Commands

The project is managed with [uv](https://docs.astral.sh/uv/) (Python >=3.12).

- `uv run main.py` — run the Python entry point
- `uv sync` — install/update the environment from `uv.lock`

There are no tests, build step, or linter configured yet. To preview the site, open `index.html` in a browser or serve the directory (e.g. `python -m http.server`).

## ORCID Sign-In

Browser-only "Sign in with ORCID" via the OpenID Connect **implicit flow** — no backend, no client secret. Files:

- `auth.py` — the PyScript module (login redirect, `id_token` validation against ORCID's JWKS, session handling).
- `orcid_config.py` — public config (sandbox defaults). `CLIENT_ID` is a public identifier; there is **no secret** in this design.
- `pyscript.toml` — loads `pyjwt`/`cryptography` and maps `orcid_config.py` into the in-browser filesystem.
- `index.html` — the sign-in button/badge and the `<script type="py" src="./auth.py" config="./pyscript.toml">` tag.

Why implicit flow: the Authorization Code flow's token exchange needs a `client_secret`, which can't live safely in a static site. The implicit flow returns the signed `id_token` directly in the redirect fragment instead. Tokens are short-lived (~10 min, `openid` scope, identity only) — re-sign-in when expired.

State is managed only through browser APIs: `window.crypto` (state/nonce), `sessionStorage` (only `{sub, name, exp}` is kept — the raw token is discarded after validation), and `history.replaceState` (strips the token from the URL).

### Setup / first run

1. Register a **public API client** in [ORCID Sandbox Developer Tools](https://sandbox.orcid.org/developer-tools) (needs a sandbox.orcid.org account). Set redirect URI `http://127.0.0.1:8000/`.
2. Put the generated **Client ID** in `orcid_config.py` (`CLIENT_ID`).
3. Enable the secret-scanning git hook once per clone: `git config core.hooksPath .githooks`.
4. Serve at the registered origin (`python -m http.server 8000`) and open `http://127.0.0.1:8000/`. Sign in with a **sandbox** test account.

### Going to production

In `orcid_config.py`, switch to the PRODUCTION block (`ORCID_BASE = https://orcid.org`, the prod redirect URI), register a matching production client, and set its `CLIENT_ID`.

### Security guardrails

- **Tokens must never be committed.** `.githooks/pre-commit` blocks any commit whose staged diff contains a JWT or a bearer-token UUID; `.gitignore` excludes `.env`/`*.token`/`*secret*`. Enable the hook (step 3 above) — it is not automatic in a fresh clone.

## Notes

- The PyScript release version is pinned in the `<link>` and `<script>` URLs in `index.html` — update both together.
- `main.py` remains a uv-generated placeholder, independent of the page.
