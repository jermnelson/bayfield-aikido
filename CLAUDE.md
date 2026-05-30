# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A website advertising Aikido classes taught by Jeremy Nelson in Bayfield, Colorado (at Elevated Martial Arts). The site is built as a single static `index.html` that loads [PyScript](https://pyscript.net/) (currently `2026.3.1`), allowing Python to run in the browser. `main.py` is the uv-generated package entry point and is currently a placeholder.

This is a very early-stage project: the page is mostly static content, and PyScript is wired up but not yet driving any behavior.

## Commands

The project is managed with [uv](https://docs.astral.sh/uv/) (Python >=3.12).

- `uv run main.py` — run the Python entry point
- `uv sync` — install/update the environment from `uv.lock`

There are no tests, build step, or linter configured yet. To preview the site, open `index.html` in a browser or serve the directory (e.g. `python -m http.server`).

## Notes

- `index.html` and `main.py` are independent today: the HTML loads PyScript from a CDN but does not reference `main.py`. If adding in-browser Python, it must be wired into the page explicitly (e.g. a `<script type="py">` tag or `<py-script>`).
- The PyScript release version is pinned in the `<link>` and `<script>` URLs in `index.html` — update both together.
