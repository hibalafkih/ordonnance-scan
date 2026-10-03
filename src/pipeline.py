import re
import unicodedata
from datetime import datetime, timedelta

import pandas as pd
from rapidfuzz import process, fuzz
from ocr import read_text
from db import engine

BASE = pd.read_sql("SELECT nom, dci, forme FROM medicaments", engine)

def norm(s):
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()

# Index de recherche : noms commerciaux + DCI
INDEX = {}
for _, r in BASE.iterrows():
    INDEX[r["nom"]] = r
    for d in str(r["dci"]).split("/"):
        INDEX.setdefault(d.strip(), r)
NOMS = list(INDEX)

ITEM = re.compile(r"^\s*\d+\s*[\)\.]\s*(.+)$")
OLD = re.compile(r"[A-Za-zÀ-ÿ]{4,}\s+\d+(?:[.,]\d+)?\s*(?:mg|g|ml|µg|ui)\b", re.I)
DOSE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|g|ml|µg|ui)\b", re.I)
NOM = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-]{2,}")
STOP = re.compile(r"signature|sp[ée]cialit|urgence", re.I)

def candidats(lignes):
    return {i for i, l in enumerate(lignes) if ITEM.match(l) or OLD.search(l)}

def extract(text):
    text = re.sub(r"(\d)\s*m[1I]\b", r"\1 ml", text)  # OCR : "180m1" -> "180 ml"
    lignes = text.splitlines()
    cands = candidats(lignes)
    resultats = []
    for i in sorted(cands):
        m = ITEM.match(lignes[i])
        contenu = m.group(1) if m else lignes[i]
        mn = NOM.search(contenu)
        if not mn:
            continue
        brut = mn.group(0)

        match = process.extractOne(brut, NOMS, scorer=fuzz.WRatio, processor=norm)
        cle, score = (match[0], round(match[1])) if match else (None, 0)
        ok = score >= 80

        d = DOSE.search(contenu)
        dosage = f"{d.group(1)} {d.group(2).lower()}" if d else None

        poso = []
        for j in range(i + 1, min(i + 5, len(lignes))):
            s = lignes[j].strip()
            if j in cands or STOP.search(s):
                break
            if not s:
                if poso:
                    break
                continue
            poso.append(s)

        resultats.append({
            "lu": brut,
            "nom": cle if ok else None,
            "confiance": score,
            "dosage": dosage,
            "posologie": " ".join(poso).replace("beures", "heures"),
            "dci": INDEX[cle]["dci"] if ok else None,
            "a_verifier": score < 90,
        })
    return resultats

MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10,
        "novembre": 11, "decembre": 12}
VALIDITE_JOURS = 90  # à adapter selon la réglementation

def _date(ligne):
    m = re.search(r"\bLe\s+(\d{1,2})/(\d{2})/(\d{4})", ligne, re.I)
    if m:
        j, mo, a = map(int, m.groups())
        return datetime(a, mo, j)
    m = re.search(r"\bLe\s+(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})", ligne, re.I)
    if m and norm(m.group(2)) in MOIS:
        return datetime(int(m.group(3)), MOIS[norm(m.group(2))], int(m.group(1)))
    return None

def controles(text):
    alertes = []
    if re.search(r"\.{5,}|…{2,}", text):
        alertes.append("Champs non remplis (pointillés détectés)")
    date_ordo = None
    for ligne in text.splitlines():
        if "né" in ligne.lower():
            continue
        try:
            date_ordo = _date(ligne)
        except ValueError:
            date_ordo = None
        if date_ordo:
            break
    if date_ordo is None:
        alertes.append("Date de l'ordonnance introuvable")
    elif datetime.now() - date_ordo > timedelta(days=VALIDITE_JOURS):
        alertes.append(f"Ordonnance ancienne ({date_ordo:%d/%m/%Y})")
    alertes.append("Signature/tampon : à vérifier visuellement")
    return alertes

if __name__ == "__main__":
    import sys, json
    chemin = sys.argv[1] if len(sys.argv) > 1 else "data/ordonnances/test1.png"
    texte = read_text(chemin)
    print(json.dumps(extract(texte), indent=2, ensure_ascii=False))
    print(controles(texte))