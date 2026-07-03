#!/usr/bin/env bash
# Render every figure to MP4. Usage:
#   ./render_all.sh          # medium quality (-qm)
#   ./render_all.sh -qh      # high quality
# Output lands under animations/media/videos/<file>/<res>/.
set -euo pipefail
MANIM="${MANIM_BIN:-manim}"
Q="${1:--qm}"

SCENES=(
  "the_seam.py TheSeam"
  "handoff.py Handoff"
  "denoise_primer.py DenoisePrimer"
  "anchor.py Anchor"
  "target.py Target"
  "soft_target.py SoftTarget"
  "action_delay.py ActionDelay"
  "timestep_signal.py TimestepSignal"
)
for s in "${SCENES[@]}"; do
  f="${s%% *}"; sc="${s##* }"
  echo "==> rendering $sc"
  # shellcheck disable=SC2086
  "$MANIM" $Q "$f" "$sc"
done
echo "Done. Next: ../scripts/make_gifs.sh to refresh the README GIFs."
