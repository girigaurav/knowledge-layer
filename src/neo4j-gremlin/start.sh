#!/usr/bin/env bash
set -euo pipefail

RUNTIME="${CONTAINER_RUNTIME:-podman}"

"$RUNTIME" run -d --name neo4j-compare \
  -p 7475:7474 -p 7688:7687 \
  -e NEO4J_AUTH=neo4j/comparepass \
  -e NEO4J_PLUGINS='["apoc","graph-data-science"]' \
   neo4j:5.26-community

"$RUNTIME" run -d --name gremlin-compare \
  -p 8182:8182 \
  tinkerpop/gremlin-server:3.7

echo "neo4j-compare:   http://localhost:7475  (bolt://localhost:7688, user=neo4j, pass=comparepass)"
echo "gremlin-compare: ws://localhost:8182/gremlin"
