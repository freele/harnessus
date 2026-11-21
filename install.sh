#!/bin/sh
# Link the skill into one or more skills directories.
# Usage: ./install.sh [skills-dir ...]    default: ~/.claude/skills
set -eu

src="$(cd "$(dirname "$0")" && pwd)/skill"
[ $# -gt 0 ] || set -- "$HOME/.claude/skills"

for dir in "$@"; do
  mkdir -p "$dir"
  if [ -e "$dir/harness" ] && [ ! -L "$dir/harness" ]; then
    echo "skipped $dir/harness: it exists and is not a link" >&2
    continue
  fi
  ln -sfn "$src" "$dir/harness"
  echo "linked $dir/harness -> $src"
done
