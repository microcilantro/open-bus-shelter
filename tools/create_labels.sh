#!/usr/bin/env bash
# Create or update the issue labels used by the feedback forms.
# Usage: tools/create_labels.sh [owner/repo]   (needs the GitHub CLI, logged in)
set -euo pipefail
REPO="${1:-microcilantro/open-bus-shelter}"

label() {
  local name="$1" color="$2" desc="$3"
  if gh api "repos/$REPO/labels" -f name="$name" -f color="$color" -f description="$desc" >/dev/null 2>&1; then
    echo "created  $name"
  else
    gh api -X PATCH "repos/$REPO/labels/$(printf %s "$name" | sed 's/ /%20/g')" \
      -f color="$color" -f description="$desc" >/dev/null && echo "updated  $name"
  fi
}

label "needs-triage"     "ededed" "New feedback, not yet reviewed"
label "structural"       "b60205" "Loads, members, connections, stability"
label "anchorage"        "d93f0b" "Post base, anchors, slab, edge distance"
label "clearance"        "fbca04" "Bus mirror, headroom, sidewalk clear path"
label "durability"       "c5def5" "Corrosion, UV, maintenance, vandalism"
label "accessibility"    "1d76db" "Wheelchair space, seating, wayfinding"
label "parts-sourcing"   "0e8a16" "Availability, local equivalents, prices, parts list"
label "manual"           "5319e7" "Assembly manual clarity and drawings"
label "regional-variant" "006b75" "Climate, code, fleet or local adaptations"
label "build-report"     "c2e0c6" "Reports from prototype builds"
label "needs-engineer"   "e99695" "Requires a licensed engineer's decision"
label "rev-b"            "bfd4f2" "Planned for the next revision"
