#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
output=${1:?Usage: probe-goldmark.sh OUTPUT_DIRECTORY}
mkdir -p "$output"
output=$(cd "$output" && pwd)
cache=$(mktemp -d /tmp/docker-goldmark-probe.XXXXXX)
export GOTOOLCHAIN=local GOMODCACHE="$cache/modules" GOCACHE="$cache/build"
cd "$repo/investigation/markdown-probe/goldmark"
go build -mod=readonly -buildvcs=false -o "$output/goldmark-probe" . > "$output/goldmark-build.log" 2>&1
go version -m "$output/goldmark-probe" > "$output/goldmark-toolchain.log"
for fixture in docker-table docker-code literal; do
  "$output/goldmark-probe" "$repo/investigation/markdown-probe/$fixture.md" > "$output/goldmark-$fixture.html"
done
echo "Probe binary/cache are setup artifacts, outside benchmark measurements: $cache"
