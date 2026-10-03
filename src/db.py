import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
URL = os.getenv("DATABASE_URL")
if not URL:
    raise RuntimeError("DATABASE_URL manquante : crée un fichier .env (voir .env.example)")
engine = create_engine(URL)