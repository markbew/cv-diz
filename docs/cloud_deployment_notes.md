# Cloud Deployment Notes

Do not upload these to GitHub:

```text
.env
real CVs
real candidate profiles
app/data/uploads/
```

Do upload:

```text
app/
scripts/
docs/
requirements.txt
README.md
```

Recommended deployment:

1. Private GitHub repo
2. Neo4j AuraDB Free
3. Streamlit Community Cloud
4. Streamlit secrets for OpenAI and Neo4j credentials
