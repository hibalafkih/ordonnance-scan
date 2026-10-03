import sys, tempfile, os
sys.path.append("src")

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from db import engine
from ocr import read_text
from pipeline import extract, controles

EXTENSIONS_OK = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

app = FastAPI(title="API Pharmacie")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"], allow_headers=["*"],
)


@app.post("/scan")
async def scan(fichier: UploadFile = File(...)):
    suffixe = os.path.splitext(fichier.filename or "")[1].lower()
    if suffixe not in EXTENSIONS_OK:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté ({suffixe or 'inconnu'}). Envoie un PNG ou un JPG.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffixe) as tmp:
        tmp.write(await fichier.read())
        chemin = tmp.name
    try:
        texte = read_text(chemin)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="Image illisible ou corrompue.")
    finally:
        os.remove(chemin)

    meds = extract(texte)
    alertes = controles(texte)

    # Le texte brut (qui contient le nom du patient) n'est pas enregistré
    with engine.begin() as c:
        oid = c.execute(text(
            "INSERT INTO ordonnances (statut) VALUES ('a_valider') RETURNING id"
        )).scalar()
        for m in meds:
            mid = None
            if m["nom"]:
                mid = c.execute(text(
                    "SELECT id FROM medicaments WHERE nom = :n OR dci = :n "
                    "ORDER BY id LIMIT 1"), {"n": m["nom"]}).scalar()
            c.execute(text(
                "INSERT INTO lignes_ordonnance "
                "(ordonnance_id, medicament_id, lu, dosage, posologie, confiance, a_verifier) "
                "VALUES (:o, :m, :lu, :d, :p, :c, :v)"),
                {"o": oid, "m": mid, "lu": m["lu"], "d": m["dosage"],
                 "p": m["posologie"], "c": m["confiance"], "v": m["a_verifier"]})

    return {"ordonnance_id": oid, "medicaments": meds, "alertes": alertes}


class Decision(BaseModel):
    pharmacien: str
    decision: str  # "validee" ou "refusee"


@app.get("/ordonnances")
def a_valider():
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT id, date_scan, statut FROM ordonnances "
            "WHERE statut = 'a_valider' ORDER BY date_scan DESC")).mappings().all()
    return [dict(r) for r in rows]


@app.get("/ordonnances/{oid}")
def detail(oid: int):
    with engine.connect() as c:
        lignes = c.execute(text(
            "SELECT * FROM lignes_ordonnance WHERE ordonnance_id = :o"),
            {"o": oid}).mappings().all()
    return [dict(r) for r in lignes]


@app.get("/stock")
def stock():
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT m.nom, s.quantite FROM stock s "
            "JOIN medicaments m ON m.id = s.medicament_id ORDER BY m.nom")
        ).mappings().all()
    return [dict(r) for r in rows]


@app.post("/ordonnances/{oid}/decision")
def decider(oid: int, d: Decision):
    if d.decision not in ("validee", "refusee"):
        raise HTTPException(status_code=400, detail="decision invalide")
    with engine.begin() as c:
        statut = c.execute(text("SELECT statut FROM ordonnances WHERE id = :o"),
                           {"o": oid}).scalar()
        if statut is None:
            raise HTTPException(status_code=404, detail="ordonnance introuvable")
        if statut != "a_valider":
            raise HTTPException(status_code=409, detail="ordonnance déjà traitée")

        if d.decision == "validee":
            lignes = c.execute(text(
                "SELECT l.medicament_id, m.nom, count(*) AS n "
                "FROM lignes_ordonnance l JOIN medicaments m ON m.id = l.medicament_id "
                "WHERE l.ordonnance_id = :o GROUP BY l.medicament_id, m.nom"),
                {"o": oid}).mappings().all()
            for l in lignes:
                r = c.execute(text(
                    "UPDATE stock SET quantite = quantite - :n "
                    "WHERE medicament_id = :m AND quantite >= :n"),
                    {"n": l["n"], "m": l["medicament_id"]})
                if r.rowcount == 0:
                    # l'exception annule toute la transaction
                    raise HTTPException(
                        status_code=409, detail=f"Stock insuffisant : {l['nom']}")

        c.execute(text("UPDATE ordonnances SET statut = :s WHERE id = :o"),
                  {"s": d.decision, "o": oid})
        c.execute(text(
            "INSERT INTO validations (ordonnance_id, pharmacien, decision) "
            "VALUES (:o, :p, :d)"), {"o": oid, "p": d.pharmacien, "d": d.decision})
    return {"ok": True}