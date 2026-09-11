#!/usr/bin/env bash
set -euo pipefail

RUNTIME="${CONTAINER_RUNTIME:-podman}"

"$RUNTIME" rm -f neo4j-compare gremlin-compare 2>/dev/null || true
