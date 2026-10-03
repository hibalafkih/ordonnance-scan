import sys, tempfile, os
sys.path.append("src")

import streamlit as st
import pandas as pd
from ocr import read_text
from pipeline import extract, controles

st.set_page_config(page_title="Scan d'ordonnance", page_icon="💊")
st.title("💊 Scan d'ordonnance")
st.caption("Outil d'aide : toute lecture doit être validée par un pharmacien.")

f = st.file_uploader("Importer une ordonnance", type=["png", "jpg", "jpeg"])

if f:
    suffixe = os.path.splitext(f.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffixe) as tmp:
        tmp.write(f.getvalue())
        chemin = tmp.name

    col1, col2 = st.columns(2)
    with col1:
        st.image(f.getvalue(), caption="Ordonnance", width="stretch")

    with col2:
        texte = read_text(chemin)
        meds = extract(texte)

        st.subheader("Alertes")
        for a in controles(texte):
            st.warning(a)

        st.subheader("Médicaments détectés")
        if not meds:
            st.warning("Aucun médicament détecté. Vérification manuelle nécessaire.")
        for m in meds:
            if m["a_verifier"]:
                st.error(f"⚠️ {m['lu']} : lecture incertaine ({m['confiance']} %)")
            else:
                st.success(f"✅ {m['nom']} {m['dosage'] or ''}".strip())
            st.write(f"**DCI :** {m['dci'] or 'inconnue'}")
            st.write(f"**Posologie :** {m['posologie'] or 'non détectée'}")

        if meds:
            st.dataframe(pd.DataFrame(meds), width="stretch")

    with st.expander("Texte brut de l'OCR"):
        st.text(texte)

    os.remove(chemin)