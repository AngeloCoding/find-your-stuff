import os
import json
import openai

# Load your OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Load schema and examples
with open('schema.json') as f:
    SCHEMA = json.load(f)

FUNCTIONS = [
    {
        "name": "execute_sql",
        "description": "Run a read-only SQL query against the primary DB and return rows.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "make_plot",
        "description": "Generate a plot from tabular data and return an image filename.",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "array", "items": {"type": "object"}},
                "config": {"type": "object"}
            },
            "required": ["data","config"]
        }
    }
]

SYSTEM_PROMPT = f"""
You are a SQL assistant for a SQLite database with the following schema and foreign keys:
{json.dumps(SCHEMA, indent=2)}
When you need to run a query, call the function execute_sql.  
If you need a diagram, call make_plot.  
Only generate SQL using SELECT statements.
"""


def ask_openai(messages):
    # Logging: print the outgoing request messages TODO del
    print("===== OpenAI Request =====")
    for msg in messages:
        role = msg.get('role')
        content = msg.get('content') if 'content' in msg else ''
        print(f"Role: {role}, Content: {content}")
    # Call the API
    print("Calling OpenAI API...")
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=FUNCTIONS,
        function_call="auto"
    )
    # Logging: print the raw API response TODO del
    print("===== OpenAI Response =====")
    print(response.choices[0].message)

    return response
