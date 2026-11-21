#!/bin/sh
# Link the skill into one or more skills directories.
# Usage: ./install.sh [skills-dir ...]    default: ~/.claude/skills
set -eu

src="$(cd "$(dirname "$0")" && pwd)/skill"
[ $# -gt 0 ] || set -- "$HOME/.claude/skills"

for dir in "$@"; do
  mkdir -p "$dir"
  if [ -e "$dir/hsus" ] && [ ! -L "$dir/hsus" ]; then
    echo "skipped $dir/hsus: it exists and is not a link" >&2
    continue
  fi
  ln -sfn "$src" "$dir/hsus"
  echo "linked $dir/hsus -> $src"
done
