from __future__ import annotations

import os

from dotenv import load_dotenv
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.environ.get("NEO4J_COMPARE_URI", "bolt://localhost:7688")
NEO4J_USERNAME = os.environ.get("NEO4J_COMPARE_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_COMPARE_PASSWORD", "comparepass")
GREMLIN_URL = os.environ.get("GREMLIN_COMPARE_URL", "ws://localhost:8182/gremlin")


def neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def gremlin_g():
    conn = DriverRemoteConnection(GREMLIN_URL, "g")
    return traversal().with_remote(conn), conn
