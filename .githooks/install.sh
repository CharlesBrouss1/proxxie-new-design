#!/usr/bin/env bash
# One-time setup: point this checkout's git hooks at .githooks/
# Run from the repo root after every fresh clone.
set -e
cd "$(dirname "$0")/.."
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
echo "✓ git hooks installed (core.hooksPath = .githooks)"
echo "  Pre-commit runs tests/test_patcher.py before every commit."
echo "  Bypass when needed: git commit --no-verify"
