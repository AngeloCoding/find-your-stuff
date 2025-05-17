# Generate Relational SQLite Database from .csv
import pandas as pd
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, Float, String, Text, ForeignKey
)

# Config
DATA_DIR = "../../data/raw/Primaerdaten"
csv_files = {
    'Kategorie'        : 'tKategorie.csv',
    'PersonenTyp'      : 'tPersonenTyp.csv',
    'Waehrung'         : 'tWaehrung.csv',
    'Verwertung'       : 'tVerwertung.csv',
    'VerwertungsZeit'  : 'tVerwertungsZeit.csv',
    'SubKategorie'     : 'tSubKategorie.csv',
    'Ort'              : 'tOrt.csv',
    'Strasse'          : 'tStrasse.csv',
    'Gegenstand'       : 'hackdays_tGegenstand.csv',
    'PersonGegenstand' : 'tPersonGegenstand.csv',
    'HistoryTyp'       : 'tHistoryTyp.csv',
    'History'          : 'tHistory.csv',
}
excel_files = {
    'Person' : 'tPerson.xlsx'
}

# Load into pandas
dfs = {}
for tbl, fn in csv_files.items():
    dfs[tbl] = pd.read_csv(f"{DATA_DIR}/{fn}", sep=';', encoding='utf-8-sig', low_memory=False)
for tbl, fn in excel_files.items():
    dfs[tbl] = pd.read_excel(f"{DATA_DIR}/{fn}", sheet_name=0)

# Define how to infer FKs
#   key:  column in child table
#   val:  "ParentTable.PrimaryKeyColumn"
fk_map = {
    'idKategorie'       : 'Kategorie.kid',
    'idPersonenTyp'     : 'PersonenTyp.ptid',
    'idWaehrung'        : 'Waehrung.wid',
    'idVerwertung'      : 'Verwertung.vid',
    'idVerwertungsZeit' : 'VerwertungsZeit.vzid',
    'idSubkategorie'    : 'SubKategorie.skid',
    'idGGST'            : 'Gegenstand.gid',
    'idPerson'          : 'Person.pid',
    'idTyp'             : 'HistoryTyp.htid',
}

# Spin up SQLAlchemy and MetaData
engine   = create_engine("sqlite:///../../data/processed/primaerdaten.db", echo=False)
metadata = MetaData()

# Dynamically declare each table
for tbl, df in dfs.items():
    cols = []
    for col in df.columns:
        # pick a SQL type based on pandas dtype
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            col_type = Integer
        elif pd.api.types.is_float_dtype(dtype):
            col_type = Float
        else:
            # strings, dates, etc. → TEXT
            col_type = Text

        # primary‐key if it's the first column and looks like "<letter>id"
        if col.lower().endswith("id") and df[col].is_unique:
            pk = True
        else:
            pk = False

        # foreign‐key?
        if col in fk_map:
            parent = fk_map[col]
            cols.append(Column(col, col_type,
                               ForeignKey(parent),
                               primary_key=pk))
        else:
            cols.append(Column(col, col_type, primary_key=pk))

    # register the table
    Table(tbl, metadata, *cols)

# Create all tables (dropping any old version)
metadata.drop_all(engine)
metadata.create_all(engine)

# Bulk‐insert data
with engine.begin() as conn:
    for tbl, df in dfs.items():
        conn.execute(
            metadata.tables[tbl].insert(),
            df.to_dict(orient="records")
        )

print("Done — built data/processed/primaerdaten.db with inferred foreign keys!")
