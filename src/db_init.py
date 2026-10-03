import pandas as pd
from sqlalchemy import text
from db import engine

SCHEMA = """
CREATE TABLE IF NOT EXISTS medicaments (
  id SERIAL PRIMARY KEY, nom TEXT NOT NULL, dci TEXT, dosage TEXT, forme TEXT);
CREATE TABLE IF NOT EXISTS stock (
  medicament_id INT REFERENCES medicaments(id), quantite INT NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS ordonnances (
  id SERIAL PRIMARY KEY, date_scan TIMESTAMP DEFAULT now(),
  texte_ocr TEXT, statut TEXT DEFAULT 'a_valider');
CREATE TABLE IF NOT EXISTS lignes_ordonnance (
  id SERIAL PRIMARY KEY, ordonnance_id INT REFERENCES ordonnances(id),
  medicament_id INT REFERENCES medicaments(id), lu TEXT, dosage TEXT,
  posologie TEXT, confiance INT, a_verifier BOOLEAN);
CREATE TABLE IF NOT EXISTS validations (
  id SERIAL PRIMARY KEY, ordonnance_id INT REFERENCES ordonnances(id),
  pharmacien TEXT, decision TEXT, date_decision TIMESTAMP DEFAULT now());
"""

with engine.begin() as c:
    for stmt in SCHEMA.split(";"):
        if stmt.strip():
            c.execute(text(stmt))
    c.execute(text("TRUNCATE medicaments RESTART IDENTITY CASCADE"))

df = pd.read_csv("data/medicaments.csv")
df.to_sql("medicaments", engine, if_exists="append", index=False)
print(f"{len(df)} médicaments importés")