# 🚀 ai-hackathon

## Project setup

Create the venv

```bash
uv venv
```

→ This will refuse if Python 3.12 isn’t installed, since we pinned ==3.12.*.

Install dependencies

```bash
uv pip install -r pyproject.toml
```

Run inside env

```bash
uv run python --version  # should show 3.12.x
uv run ipython
```

Lock dependencies (optional but recommended)

```bash
uv lock
```

→ Generates uv.lock with all resolved versions.