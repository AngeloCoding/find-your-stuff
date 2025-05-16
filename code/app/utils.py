import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import uuid

def execute_sql(query: str, db_path: str = "primaerdaten.db") -> list:
    """
    Execute a read-only SQL SELECT query against the SQLite DB and return rows as list of dicts.
    """
    # Basic sanitization: only allow SELECT statements
    q = query.strip().lower()
    if not q.startswith('select'):
        raise ValueError('Only SELECT queries are allowed.')
    if 'pragma' in q or 'attach' in q or 'drop' in q or 'alter' in q:
        raise ValueError('Unsafe SQL detected.')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


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
