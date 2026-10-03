"use client";
import { useState } from "react";
import type { ScanResponse, Decision } from "@/types";

const API_URL = "http://localhost:8000";
const USE_MOCK = false; // true pour travailler sans l'API

const MOCK: ScanResponse = {
  ordonnance_id: 0,
  medicaments: [
    { lu: "DOLIPRANE", nom: "Doliprane", confiance: 100, dosage: "500 mg",
      posologie: "1 comprimé en cas de douleur", dci: "Paracétamol", a_verifier: false },
  ],
  alertes: ["Signature/tampon : à vérifier visuellement"],
};

export default function Page() {
  const [res, setRes] = useState<ScanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [pharmacien, setPharmacien] = useState("");
  const [decision, setDecision] = useState<Decision | null>(null);

  async function envoyer(e: React.ChangeEvent<HTMLInputElement>) {
    const fichier = e.target.files?.[0];
    if (!fichier) return;
    setLoading(true);
    setErreur(null);
    setDecision(null);
    try {
      if (USE_MOCK) {
        setRes(MOCK);
      } else {
        const body = new FormData();
        body.append("fichier", fichier);
        const r = await fetch(`${API_URL}/scan`, { method: "POST", body });
        if (!r.ok) throw new Error(`Erreur API ${r.status}`);
        setRes((await r.json()) as ScanResponse);
      }
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  async function decider(d: Decision) {
    if (!res) return;
    if (!pharmacien.trim()) {
      setErreur("Indique le nom du pharmacien avant de décider.");
      return;
    }
    setErreur(null);
    try {
      if (!USE_MOCK) {
        const r = await fetch(`${API_URL}/ordonnances/${res.ordonnance_id}/decision`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pharmacien: pharmacien.trim(), decision: d }),
        });
        if (!r.ok) throw new Error(`Erreur API ${r.status}`);
      }
      setDecision(d);
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Erreur inconnue");
    }
  }

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-1 text-2xl font-bold">💊 Scan d&apos;ordonnance</h1>
      <p className="mb-4 text-sm text-gray-500">
        Outil d&apos;aide : toute lecture doit être validée par un pharmacien.
      </p>

<input type="file" accept=".png,.jpg,.jpeg" onChange={envoyer} className="mb-4" />
      {loading && <p>Analyse en cours…</p>}
      {erreur && <p className="text-red-600">{erreur}</p>}

      {res?.alertes.map((a, i) => (
        <p key={i} className="mb-1 rounded bg-yellow-100 p-2 text-sm">⚠️ {a}</p>
      ))}

      {res && res.medicaments.length === 0 && (
        <p className="mt-3 rounded bg-yellow-100 p-2 text-sm">
          Aucun médicament détecté. Vérification manuelle nécessaire.
        </p>
      )}

      {res?.medicaments.map((m, i) => (
        <div key={i}
          className={`mt-3 rounded border p-3 ${m.a_verifier ? "bg-red-50" : "bg-green-50"}`}>
          <p className="font-semibold">
            {m.a_verifier ? "⚠️ " : "✅ "}{m.nom ?? m.lu} {m.dosage ?? ""}
            <span className="ml-2 text-sm font-normal">({m.confiance} %)</span>
          </p>
          <p className="text-sm">DCI : {m.dci ?? "inconnue"}</p>
          <p className="text-sm">Posologie : {m.posologie || "non détectée"}</p>
        </div>
      ))}

      {res && (
        <section className="mt-6 rounded border p-3">
          <h2 className="mb-2 font-semibold">Validation du pharmacien</h2>
          {decision ? (
            <p className={decision === "validee" ? "text-green-700" : "text-red-700"}>
              Ordonnance {decision === "validee" ? "validée" : "refusée"}.
            </p>
          ) : (
            <>
              <input
                value={pharmacien}
                onChange={(e) => setPharmacien(e.target.value)}
                placeholder="Nom du pharmacien"
                className="mb-2 w-full rounded border p-2 text-sm"
              />
              <div className="flex gap-2">
                <button onClick={() => decider("validee")}
                  className="rounded bg-green-600 px-3 py-1 text-white">
                  Valider
                </button>
                <button onClick={() => decider("refusee")}
                  className="rounded bg-red-600 px-3 py-1 text-white">
                  Refuser
                </button>
              </div>
            </>
          )}
        </section>
      )}
    </main>
  );
}