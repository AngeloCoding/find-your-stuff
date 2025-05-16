import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import uuid
from typing import List, Dict, Any

def execute_sql(query: str, db_path: str = "primaerdaten.db") -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL SELECT query against the SQLite DB and return rows as list of dicts.
    Allows one optional trailing semicolon but rejects multi-statement queries or forbidden keywords.
    """
    # 1) Normalize whitespace & strip trailing semicolon
    raw = query.strip()
    if raw.endswith(';'):
        raw = raw[:-1].strip()

    # 2) Must start with SELECT
    low = raw.lower()
    if not low.startswith('select'):
        raise ValueError('Only SELECT queries are allowed.')

    # 3) Reject any semicolons (now guaranteed no trailing one) or dangerous keywords
    if ';' in raw:
        raise ValueError('Multiple statements detected.')
    for forbidden in ('pragma ', 'attach ', 'drop ', 'alter ', 'insert ', 'update ', 'delete '):
        if forbidden in low:
            raise ValueError(f'Unsafe SQL detected: contains "{forbidden.strip()}"')

    # 4) Run query safely
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(raw)
        rows = cur.fetchall()

    rows = rows[:20]  # Limit to 20 rows for performance

    # 5) Convert to list of dicts
    return [dict(r) for r in rows]


def make_plot(data: list, config: dict) -> str:
    """
    Generate a plot from data and save to a temporary file.
    config: { type: 'bar'|'line'|'pie', x: column, y: column }
    Returns path to saved image.
    """
    df = pd.DataFrame(data)
    if config['type'] == 'bar':
        fig, ax = plt.subplots()
        ax.bar(df[config['x']], df[config['y']])
    elif config['type'] == 'line':
        fig, ax = plt.subplots()
        ax.plot(df[config['x']], df[config['y']])
    elif config['type'] == 'pie':
        fig, ax = plt.subplots()
        ax.pie(df[config['y']], labels=df[config['x']], autopct='%1.1f%%')
    else:
        raise ValueError(f"Unknown plot type: {config['type']}")
    fname = f"plot_{uuid.uuid4().hex}.png"
    fig.savefig(fname, bbox_inches='tight')
    plt.close(fig)
    return fname
