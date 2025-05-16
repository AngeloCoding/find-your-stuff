# SQLite QA Agent

This Streamlit app lets you ask natural-language questions about a SQLite database.
It uses OpenAI's function-calling to safely generate SQL and plots.

## Setup

1. Create a virtual env: `python -m venv venv`
2. `pip install -r requirements.txt`
3. Set `OPENAI_API_KEY` env var.
4. Place `primaerdaten.db` next to these files.

## Run

```bash
cd code/app
```
```bash
streamlit run app.py
```
