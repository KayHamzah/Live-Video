#!/bin/bash
# Render every spec: tools/render_all.sh <transcript.jsonl> <source.mp4> <outdir> [spec...]
set -e
T=$1; SRC=$2; OUT=$3; shift 3
SPECS=${@:-$(ls "$(dirname "$0")"/../specs/*.json)}
for s in $SPECS; do
  n=$(basename "$s" .json)
  python3 "$(dirname "$0")/render.py" "$s" "$T" "$SRC" "$OUT/$n.mp4"
done
