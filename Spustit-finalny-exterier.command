#!/bin/zsh
set -e

# Open the current verified final app through the same entry as npm run unreal:open.
project_dir="${0:A:h}"
cd "$project_dir"
exec /usr/bin/env node "$project_dir/scripts/unreal/open-current.mjs" "$@"
