import sqlite3
import time
import requests
import os
import json

USER_AGENT = "MeinFundsachenScript/1.0 (pfisd4@bfh.ch)" 

def geocode_address(fundort, fundplz, fundstrasse):
    address = f"{fundstrasse}, {fundplz} {fundort}, Schweiz"
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 0,
        "limit": 1,
    }
    headers = {
        "User-Agent": USER_AGENT
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        else:
            print(f"Kein Ergebnis für Adresse: {address}")
            return None, None
    except Exception as e:
        print(f"Fehler beim Geocoding: {e}")
        return None, None

def create_new_db(db_name="fundsachen_neu.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS fundsache (
        id INTEGER PRIMARY KEY,
        beschreibung TEXT,
        funddatum TEXT,
        fundstrasse TEXT,
        fundplz TEXT,
        fundort TEXT,
        lat REAL,
        lon REAL,
        kategorie TEXT,
        subkategorie TEXT,
        wert REAL
    )
    ''')
    conn.commit()
    conn.close()

def transfer_data(old_db="alte_datenbank.db", new_db="fundsachen_neu.db", limit=20, offset=0):
    old_conn = sqlite3.connect(old_db)
    old_c = old_conn.cursor()

    new_conn = sqlite3.connect(new_db)
    new_c = new_conn.cursor()

    query = f'''
    SELECT g.gid, g.Beschreibung, g.FundDatum, g.FundStrasse, g.FundPLZ, g.FundOrt, 
           k.Beschreibung AS Kategorie, sk.Beschreibung AS Subkategorie, g.Wert
    FROM Gegenstand g
    LEFT JOIN SubKategorie sk ON g.idSubkategorie = sk.skid
    LEFT JOIN Kategorie k ON sk.idKategorie = k.kid
    LIMIT {limit} OFFSET {offset}
    '''

    old_c.execute(query)
    rows = old_c.fetchall()

    for i, row in enumerate(rows):
        gid, beschreibung, funddatum, fundstrasse, fundplz, fundort, kategorie, subkategorie, wert = row

        if fundort and fundplz and fundstrasse:
            # lat, lon = geocode_address(fundort, fundplz, fundstrasse)
            # time.sleep(1.5)  # Nominatim-Richtlinie: 1 Anfrage pro Sekunde
            lat, lon = None, None
        else:
            lat, lon = None, None

        new_c.execute('''
            INSERT OR REPLACE INTO fundsache 
            (id, beschreibung, funddatum, fundstrasse, fundplz, fundort, lat, lon, kategorie, subkategorie, wert)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (gid, beschreibung, funddatum, fundstrasse, str(fundplz), fundort, lat, lon, kategorie, subkategorie, wert))

        print(f"{offset + i + 1}/{offset + limit}: Eingetragen ID {gid} mit Koordinaten ({lat}, {lon})")

    new_conn.commit()
    old_conn.close()
    new_conn.close()


def export_to_json(db_path, json_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM fundsache")
    rows = c.fetchall()
    columns = [description[0] for description in c.description]

    data = [dict(zip(columns, row)) for row in rows]

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    conn.close()
    print(f"Daten exportiert nach {json_path}")
    
import csv
import sqlite3

def fill_missing_coordinates_from_csv(db_path, plz_csv_path):
    # Lade PLZ -> Koordinaten aus CSV in ein Dictionary
    plz_coords = {}
    with open(plz_csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                plz = row['zip'].strip()
                lat = float(row['lat'])
                lon = float(row['lng'])
                plz_coords[plz] = (lat, lon)
            except (ValueError, KeyError):
                print(f"Ungültige Zeile in CSV: {row}")
                continue  # Ignoriere unvollständige oder ungültige Zeilen

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Wähle alle Einträge ohne Koordinaten
    c.execute("""
        SELECT id, fundplz FROM fundsache 
        WHERE lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0
    """)

    rows = c.fetchall()

    updated = 0
    for id_, plz in rows:
        if not plz:
            continue
        coords = plz_coords.get(plz.strip())
        if coords:
            lat, lon = coords
            c.execute("UPDATE fundsache SET lat = ?, lon = ? WHERE id = ?", (lat, lon, id_))
            updated += 1

    conn.commit()
    conn.close()
    print(f"{updated} Einträge mit Koordinaten aus PLZ-CSV ergänzt.")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    old_db_path = os.path.abspath(os.path.join(script_dir, '..', '..', 'data', 'processed', 'primaerdaten.db'))
    new_db_path = os.path.join(script_dir, 'fundsachen_mit_geo.db')
    json_output_path = os.path.join(script_dir, 'fundsachen_export.json')
    plz_csv_path = os.path.join(script_dir, 'post-codes.csv')

    create_new_db(new_db_path)
    transfer_data(old_db=old_db_path, new_db=new_db_path, limit=60000, offset=0)
    print("Daten übertragen mit echten Geodaten.")
    fill_missing_coordinates_from_csv(new_db_path, plz_csv_path)
    export_to_json(db_path=new_db_path, json_path=json_output_path)
