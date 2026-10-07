#!/usr/bin/env bash
set -euo pipefail
# Native equivalent of Dockerfile build + pagefind + release stages.
upstream=${1:?Usage: build-upstream.sh UPSTREAM OUTPUT EVIDENCE TOOLS}
output=${2:?}
evidence=${3:?}
tools=${4:?}
upstream=$(realpath "$upstream")
output=$(realpath -m "$output")
evidence=$(realpath -m "$evidence")
tools=$(realpath "$tools")
mkdir -p "$evidence"
if [[ -e "$output" ]]; then
  echo 'Use a new output directory; baseline artifacts must be preserved.' >&2
  exit 1
fi
export PATH="$tools/node-v24.21.0-linux-x64/bin:$tools:$PATH"
export HUGO_CACHEDIR="$evidence/hugo-cache"
export NODE_ENV=production
cd "$upstream"
expected_sha=6cf1b1c167f032e8a6629da211602300b623b20e
if [[ $(git rev-parse HEAD) != "$expected_sha" || $(git rev-parse --is-shallow-repository) != false ]]; then
  echo "Expected pinned commit $expected_sha with full Git history." >&2
  exit 1
fi
git diff --exit-code
git diff --cached --exit-code
git rev-parse HEAD > "$evidence/upstream-sha.txt"
{ hugo version; node --version; npm --version; GOTOOLCHAIN=local go version; uname -a; } > "$evidence/versions.txt"
run() {
  local name=$1
  shift
  printf '%q ' "$@" > "$evidence/$name.command"
  printf '\n' >> "$evidence/$name.command"
  /usr/bin/time -v -o "$evidence/$name.time" "$@" > "$evidence/$name.log" 2>&1
}
run hugo hugo --gc --minify --panicOnWarning --printPathWarnings --printUnusedTemplates -b https://docs.docker.com -e production --destination "$output"
run flatten-tests node --test hack/test/flatten-and-resolve.mjs
run flatten node hack/flatten-and-resolve.js "$output"
run api-verify node hack/api-docs/verify-output.mjs "$output"
run pagefind npx --yes pagefind@1.5.2 --site "$output" --output-path "$output/pagefind"
git status --porcelain > "$evidence/upstream-status.txt"
