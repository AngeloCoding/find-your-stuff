import os
import json
import openai
import logging

# configure logger
# logging.basicConfig(
#     filename='app.log',
#     filemode='a',
#     format='%(asctime)s %(levelname)s:%(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     level=logging.DEBUG
# )
logger = logging.getLogger(__name__)

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
You are a SQL assistant for a SQLite database stored in primaerdaten.db.  
Below is the schema (table → columns, and foreign-key relationships), followed by detailed meanings for every coded or lookup column.  When answering questions, generate only SELECT statements or explicitly call execute_sql; use joins whenever you need human-readable labels for codes.

Schema:
{json.dumps(SCHEMA, indent=2)}

Foreign keys:
- Gegenstand.idSubkategorie → SubKategorie.kid  
- SubKategorie.idKategorie → Kategorie.kid  
- Gegenstand.idVerwertung → Verwertung.vid  
- Gegenstand.idVerwertungsZeit → VerwertungsZeit.vzid  
- Gegenstand.idWaehrung → Waehrung.wid  
- Gegenstand.FundStrasse → Strasse.sid  
- PersonGegenstand.idGGST → Gegenstand.gid  
- PersonGegenstand.idPerson → Person.pid  
- History.idGGST → Gegenstand.gid  
- History.idPerson → Person.pid  
- History.idTyp → HistoryTyp.htid  

Column reference:

**Gegenstand** (items)  
- **gid**: unique item ID  
- **FundbuchNr**: inventory/book number  
- **idSubkategorie** → SubKategorie.kid → SubKategorie.Name → Kategorie via SubKategorie.idKategorie  
- **Beschreibung**, **Material**, **Farbe**, **Inhalt**: free-text descriptors  
- **Natel** (0 = not a mobile phone, 1 = smartphone)  
- **NatelProvider**, **NatelTyp**: only populated if Natel=1; mobile operator name and device model  
- **FundDatum**: ISO datetime when found  
- **FundOrt**: free-text place name  
- **FundPLZ**: postal code  
- **FundStrasse** → Strasse.sid → Strasse.Strassenbezeichnung  
- **Wert**: estimated value  
- **idWaehrung** → Waehrung.wid (1=CHF, 2=EUR, 3=USD)  
- **FinderlohnJaNein** (0=no finder’s fee, 1=fee due)  
- **FinderlohnOblig**, **FinderlohnFrei**, **Gebuehren**, **VersteigerungErtrag**: monetary fee and auction revenue fields  
- **GGSTErhalten**: datetime when item was received into storage  
- **GGSTErhaltenPerson** (0=not yet collected, 1=collected by finder)  
- **FLErhalten**, **VSTWErhalten**, **GGSTVerwertet**, **FLVerwertet**, **GGSTBei**, **VSTWAusbezahlt**, **VSTWAusbezahltPerson**: various datetime or flag fields tracking processing steps  
- **Lagerort**: storage location  
- **idVerwertung** → Verwertung.vid (1=Entsorgen, 2=Versteigern, 3=Weiterleiten, 4=Retour an Finder)  
- **idVerwertungsZeit** → VerwertungsZeit.vzid (“3 Monate”=1, “6 Monate”=2, “1 Jahr”=3, “5 Jahre”=4)  
- **DatVerwertung**: disposal date  
- **ErfasstDatum**, **MutiertDatum**: record created/modified timestamps  
- **Status**: lifecycle code (–1/0/1/2)

**PersonGegenstand** (relations)
- **pgid**: unique  
- **idGGST** → Gegenstand.gid  
- **idPerson** → Person.pid  
- **FinderVerlierer** (0=item was lost, 1=found)

**Person**
- **pid**, **Vorname**, **Name**, **idOrt** → Ort.oid

**SubKategorie**, **Kategorie**
- Sub- and top-level categorization (ids → names)

**Verwertung**, **VerwertungsZeit**, **Waehrung**, **Strasse**, **Ort**, **HistoryTyp**
- Lookup tables (id → Beschreibung, plus template names in HistoryTyp.Dot)

**History** (audit/log)
- **hid**, **idGGST**, **idPerson**, **Datum**  
- **Beschreibung**: free-text note  
- **idTyp** → HistoryTyp.htid → HistoryTyp.Beschreibung (predefined event types)

Always join to the appropriate lookup table to turn any `idXxx` or flag into its human-readable label.  Only use `SELECT`; for diagrams call `make_plot`.  
"""


def ask_openai(messages):
    # Call the API
    logger.debug("Sending to OpenAI: %s", messages)
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=FUNCTIONS,
        function_call="auto"
    )
    logger.debug("Response from OpenAI: %s", response)
    return response
