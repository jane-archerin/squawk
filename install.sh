#!/usr/bin/env bash
# Install `squawk` as a command on your PATH by symlinking it into a bin dir.
# Zero dependencies — it just links this repo's launcher so `squawk` works
# from any project directory. Re-run after moving the repo.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/squawk"
chmod +x "$SRC"

# Prefer ~/.local/bin (no sudo); fall back to /usr/local/bin.
if [[ -d "$HOME/.local/bin" ]] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
  BIN="$HOME/.local/bin"
elif [[ -w /usr/local/bin ]]; then
  BIN="/usr/local/bin"
else
  echo "No writable bin dir found. Create ~/.local/bin or run with a writable /usr/local/bin." >&2
  exit 1
fi

ln -sf "$SRC" "$BIN/squawk"
echo "Linked: $BIN/squawk -> $SRC"

if ! command -v squawk >/dev/null 2>&1; then
  echo
  echo "⚠  $BIN is not on your PATH yet. Add this to your shell profile"
  echo "   (~/.zshrc or ~/.bashrc), then restart your terminal:"
  echo
  echo "     export PATH=\"$BIN:\$PATH\""
else
  echo "Done. From any project directory, run:  squawk"
fi
