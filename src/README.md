# Scan d'ordonnance

Application de pharmacie qui lit une ordonnance (image), extrait les médicaments,
les valide contre une base de référence et aide le pharmacien à la validation
et à la gestion du stock.

> Outil d'aide uniquement : toute lecture doit être validée par un pharmacien.

## Fonctionnalités
- OCR (Tesseract + OpenCV) et extraction du nom, dosage et posologie
- Correspondance floue avec la base de médicaments (RapidFuzz)
- Alertes : ordonnance ancienne, champs vides, signature à vérifier
- API FastAPI + base PostgreSQL (ordonnances, validations, stock)
- Validation / refus par le pharmacien, décrémentation du stock
- Interface Next.js (TypeScript)

## Stack
Python, FastAPI, SQLAlchemy, PostgreSQL, Tesseract, OpenCV, RapidFuzz,
Next.js, React, TypeScript, Tailwind CSS

## Installation
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
1. Installer Tesseract (build UB Mannheim) avec le pack de langue `fra`.
2. Créer la base `pharmacie`, copier `.env.example` en `.env` et renseigner le mot de passe.
3. Initialiser la base : `python src\db_init.py`

## Lancement
```bat
uvicorn main:app --reload
cd frontend
npm install
npm run dev
```
API : http://localhost:8000/docs, front : http://localhost:3000

## Limites
- Tesseract lit mal l'écriture manuscrite
- Pas d'authentification pour l'instant
- Base de médicaments de démonstration (à remplacer par une source officielle)
- Aucune donnée réelle de patient ne doit être utilisée