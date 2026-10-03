export interface Medicament {
  lu: string;
  nom: string | null;
  confiance: number;
  dosage: string | null;
  posologie: string;
  dci: string | null;
  a_verifier: boolean;
}

export interface ScanResponse {
  ordonnance_id: number;
  medicaments: Medicament[];
  alertes: string[];
}

export type Decision = "validee" | "refusee";