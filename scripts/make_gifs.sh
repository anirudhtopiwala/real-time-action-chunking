#!/usr/bin/env bash
# Convert the rendered MP4s into optimized GIFs in assets/ (used by the README).
# Run after animations/render_all.sh. Requires ffmpeg. Portable to bash 3.2 (macOS).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# file-stem : gif-handle : scene-class
PAIRS=(
  "the_seam:the-seam:TheSeam"
  "handoff:handoff:Handoff"
  "denoise_primer:denoise-primer:DenoisePrimer"
  "single_action:single-action:SingleAction"
  "full_prefix:full-prefix:FullPrefix"
  "action_delay:action-delay:ActionDelay"
  "timestep_signal:timestep-signal:TimestepSignal"
)
for p in "${PAIRS[@]}"; do
  IFS=: read -r stem handle cls <<< "$p"
  mp4="$(find "$ROOT/animations/media/videos/$stem" -name "$cls.mp4" 2>/dev/null | head -1)"
  if [ -n "$mp4" ]; then
    ffmpeg -y -i "$mp4" -vf "fps=12,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
      "$ROOT/assets/$handle.gif"
    echo "  wrote assets/$handle.gif"
  else
    echo "  (skip $handle, render it first)"
  fi
done
