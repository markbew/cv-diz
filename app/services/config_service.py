"""
Config helper for CV-Diz.

Reads secrets from Streamlit Cloud first, then falls back to local .env variables.

Local development:
    .env

Streamlit Cloud:
    App settings -> Secrets
"""

import os
import streamlit as st


def get_secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass

    return os.getenv(name, default)


def get_openai_api_key() -> str:
    return get_secret("OPENAI_API_KEY")


def get_neo4j_uri() -> str:
    return get_secret("NEO4J_URI", "bolt://localhost:7687")


def get_neo4j_username() -> str:
    return get_secret("NEO4J_USERNAME", "neo4j")


def get_neo4j_password() -> str:
    return get_secret("NEO4J_PASSWORD")
