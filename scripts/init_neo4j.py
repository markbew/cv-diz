"""
Initialise CV-Diz Neo4j constraints.

Run from project root:
    python scripts/init_neo4j.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app"
sys.path.append(str(APP_PATH))

from services.neo4j_service import Neo4jService  # noqa: E402


def main():
    load_dotenv(ROOT / ".env")
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError("NEO4J_PASSWORD missing from .env")
    service = Neo4jService(uri=uri, username=username, password=password)
    try:
        service.verify_connectivity()
        service.initialise_constraints()
        print("CV-Diz Neo4j constraints initialised.")
    finally:
        service.close()


if __name__ == "__main__":
    main()
