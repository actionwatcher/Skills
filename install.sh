#!/usr/bin/env bash
# Link each skill in this repo into the Claude Code and Codex skills folders.
# A real folder (not a link) with the same name moves to a backup folder first.
# Usage: ./install.sh [--dry-run]

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS=("$HOME/.claude/skills" "$HOME/.codex/skills")
BACKUP_DIR="$HOME/.skills-backup/$(date +%Y%m%d-%H%M%S)"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--dry-run]" >&2
  exit 2
fi

run() {
  if (( DRY_RUN )); then
    echo "  [dry-run] $*"
  else
    "$@"
  fi
}

shopt -s nullglob
skills=()
for dir in "$REPO_DIR"/*/; do
  [[ -f "$dir/SKILL.md" ]] && skills+=("${dir%/}")
done

if (( ${#skills[@]} == 0 )); then
  echo "No skills found in $REPO_DIR" >&2
  exit 1
fi

for target in "${TARGETS[@]}"; do
  echo "== $target"
  run mkdir -p "$target"

  for src in "${skills[@]}"; do
    name="$(basename "$src")"
    dest="$target/$name"

    if [[ -L "$dest" ]]; then
      if [[ "$(readlink "$dest")" == "$src" ]]; then
        echo "  ok       $name"
        continue
      fi
      echo "  relink   $name (was -> $(readlink "$dest"))"
      run rm "$dest"
    elif [[ -e "$dest" ]]; then
      backup="$BACKUP_DIR/$(basename "$(dirname "$target")")/$name"
      echo "  backup   $name -> $backup"
      run mkdir -p "$(dirname "$backup")"
      run mv "$dest" "$backup"
    else
      echo "  link     $name"
    fi

    run ln -s "$src" "$dest"
  done
done

echo "Done. Start a new Claude Code or Codex session to load the skills."
