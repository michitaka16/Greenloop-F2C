---
type: DISCOVERY
date: 2026-04-17
created_at: 2026-04-17T14:30:00Z
author: agent
session_id: 01358dfa-9027-4e11-a69e-056289852b5a
session_turn: 10
project: greenloop-f2c
topic: uv sync --frozen creates UF_HIDDEN pth files on macOS
phase: implement
tags: [ci, macos, uv, python, pth-files]
---

# `uv sync --frozen` causes UF_HIDDEN on macOS editable .pth files

## Discovery

`uv sync --frozen` (without `--extra dev`) was used in CI. On macOS, this reliably creates `__editable__` `.pth` files with the BSD `UF_HIDDEN` flag set. Python 3.12's `site.py:addpackage()` skips any `.pth` file where `st_flags & stat.UF_HIDDEN` is true.

The result: `uv pip list` shows the package installed, `greenloop-farm-os` is in the dist-info, the `.pth` file exists with the correct path — but `import greenloop` fails with `ModuleNotFoundError` because Python silently skips the file.

## Why this was hard to find

The `python -v` output explicitly says "Skipping hidden .pth file" — but the path to reproducing it required running `uv sync --frozen` inside a fresh venv. The symptom (ModuleNotFoundError with correct dist-info) looks like a broken editable install, not a filesystem attribute issue.

## For Discussion

- **Counterfactual**: If the CI had not used `--frozen` from the start (plain `uv sync --extra dev`), this bug would never have surfaced. Is `--frozen` providing enough reproducibility value to justify the risk, given that `uv.lock` already pins versions?
- **Data reference**: On this Mac (macOS, APFS, Python 3.12.13 via uv 0.11.6), `--frozen` consistently produces `UF_HIDDEN` on .pth files. The question is whether this affects all macOS users, all uv editable installs, or only this specific filesystem/uv version combination. What is the prevalence among users of this repo?
- **Root cause**: `python -v` output confirmed: "Skipping hidden .pth file: `.../__editable__.greenloop_farm_os-0.1.0.pth`" with `stat.UF_HIDDEN` set on the file. This is Python's site.py behavior (lines 176–179). The question is whether uv's `--frozen` is the root cause, or whether it's a macOS filesystem policy that uv is not accounting for. Does `--frozen` create files differently than plain `uv sync`?
