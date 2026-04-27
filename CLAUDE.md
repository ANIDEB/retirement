# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e . -r requirements-dev.txt
```

## Commands

```bash
# Run all tests (enforces 100% coverage)
.venv/bin/pytest

# Run a single test
.venv/bin/pytest tests/test_greeting.py::test_greet_default

# Run the app
python3 main.py
```

## Architecture

The package lives in `src/retirement/` (src layout) and is installed in editable mode so `import retirement` works from the repo root. `main.py` is the entry point and sits at the root (outside `src/`) — it is also tracked by coverage.

100% test coverage is enforced via `--cov-fail-under=100` in `pyproject.toml`. The `if __name__ == "__main__":` guard in `main.py` is marked `# pragma: no cover` because it runs in a subprocess and cannot be tracked by pytest-cov.

## Directory conventions

- `src/retirement/` — application source modules
- `tests/` — mirrors the module structure in `src/retirement/`
- `data/input/` — user-provided input files (gitignored)
- `data/output/` — application-generated output files (gitignored)
- `prompts/` — LLM prompts that drive application behaviour (version-controlled)
