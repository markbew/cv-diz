# CV-Diz v0.6.1 Cloud-Ready Patch

This patch adds:

```text
app/services/config_service.py
```

It lets the app read secrets from:

1. Streamlit Cloud secrets
2. local `.env`

## Small code edits needed in `app/app.py`

### 1. Add this import near the other service imports:

```python
from services.config_service import (
    get_openai_api_key,
    get_neo4j_uri,
    get_neo4j_username,
    get_neo4j_password,
)
```

### 2. In `get_neo4j_service()`, replace:

```python
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "")
```

with:

```python
uri = get_neo4j_uri()
username = get_neo4j_username()
password = get_neo4j_password()
```

### 3. In `call_openai_text()`, replace:

```python
api_key = os.getenv("OPENAI_API_KEY")
```

with:

```python
api_key = get_openai_api_key()
```

## Streamlit Cloud secrets format

Paste this into Streamlit Cloud secrets:

```toml
OPENAI_API_KEY = "your_openai_key"
NEO4J_URI = "neo4j+s://your-aura-uri.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_aura_password"
```
