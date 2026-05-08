"""
Moteur CF item-item — recommande uniquement les plats disponibles localement.
"""
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os

class Recommender:

    def __init__(self, data_dir="."):
        self.data_dir = data_dir
        self._fitted  = False

    def fit(self):
        self.plats = pd.read_csv(f"{self.data_dir}/plats.csv")
        self.notes = pd.read_csv(f"{self.data_dir}/notes.csv")
        self._build_sim()
        self._fitted = True
        return self

    def _build_sim(self, extra_notes: dict = None):
        notes = self.notes.copy()
        if extra_notes:
            rows = [{"user_id": 0, "meal_id": mid, "note": n}
                    for mid, n in extra_notes.items()]
            notes = pd.concat([notes, pd.DataFrame(rows)], ignore_index=True)
        matrix  = notes.pivot_table(index="user_id", columns="meal_id", values="note")
        centered = matrix.sub(matrix.mean(axis=1), axis=0).fillna(0)
        sim      = cosine_similarity(centered.T)
        self.sim_df = pd.DataFrame(sim, index=matrix.columns, columns=matrix.columns)
        self.matrix = matrix

    def _filtrer_base(self, allergies: list, piment_max: int,
                      saison: str, meal_ids_locaux: set = None) -> pd.DataFrame:
        """Applique les filtres communs : allergies, piment, saison, localisation."""
        df = self.plats.copy()

        # Filtre localisation — PRIORITAIRE
        if meal_ids_locaux is not None:
            df = df[df["meal_id"].isin(meal_ids_locaux)]

        # Filtre allergies
        for alg in allergies:
            df = df[~df["allergenes"].str.contains(alg, case=False, na=False)]

        # Filtre piment
        df = df[df["piment"] <= piment_max]

        # Filtre saison
        df = df[df["saison"].isin([saison, "toutes"])]

        return df

    def recommander(self, cuisine_pref: str, allergies: list, piment_max: int,
                    saison: str, notes_user: dict = None,
                    meal_ids_locaux: set = None, n: int = 8) -> pd.DataFrame:
        """
        Recommande n plats disponibles localement.
        meal_ids_locaux : ensemble des meal_ids servis dans les restos de la ville.
        """
        if notes_user:
            self._build_sim(extra_notes=notes_user)

        df = self._filtrer_base(allergies, piment_max, saison, meal_ids_locaux)

        if notes_user:
            df = df[~df["meal_id"].isin(notes_user.keys())]

        if df.empty:
            return pd.DataFrame()

        # Score CF si notes disponibles
        if notes_user and 0 in self.matrix.index:
            scores = {}
            for mid in df["meal_id"]:
                if mid not in self.sim_df.columns:
                    scores[mid] = 0.0
                    continue
                rated = {m: v for m, v in notes_user.items() if m in self.sim_df.index}
                if not rated:
                    scores[mid] = 0.0
                    continue
                sims = self.sim_df[mid][list(rated.keys())]
                pos  = sims[sims > 0]
                if pos.empty:
                    scores[mid] = 0.0
                    continue
                scores[mid] = (pos * pd.Series(rated)[pos.index]).sum() / pos.sum()
            df["score"] = df["meal_id"].map(scores).fillna(0)
        else:
            # Cold start : popularité
            pop = (
                self.notes[self.notes["meal_id"].isin(df["meal_id"])]
                .groupby("meal_id")["note"]
                .agg(moyenne="mean", cnt="count")
            )
            pop["score"] = pop["moyenne"] * np.log1p(pop["cnt"])
            df = df.merge(pop[["score"]], on="meal_id", how="left")
            df["score"] = df["score"].fillna(0)

        # Boost cuisine préférée
        df.loc[df["cuisine"] == cuisine_pref, "score"] *= 1.30

        return df.sort_values("score", ascending=False).head(n).reset_index(drop=True)

    def candidats_a_noter(self, cuisine_pref: str, allergies: list,
                          piment_max: int, saison: str,
                          meal_ids_locaux: set = None, n: int = 10) -> pd.DataFrame:
        """Sélectionne n plats variés à faire noter — filtrés localement."""
        df = self._filtrer_base(allergies, piment_max, saison, meal_ids_locaux)

        if df.empty:
            return pd.DataFrame()

        pref  = df[df["cuisine"] == cuisine_pref]
        other = df[df["cuisine"] != cuisine_pref]

        n_pref  = min(int(n * 0.6), len(pref))
        n_other = min(n - n_pref, len(other))

        return pd.concat([
            pref.sample(n_pref,   random_state=42) if n_pref  > 0 else pd.DataFrame(),
            other.sample(n_other, random_state=42) if n_other > 0 else pd.DataFrame(),
        ]).reset_index(drop=True)

    def similaires(self, meal_id: int, n: int = 5) -> pd.DataFrame:
        if meal_id not in self.sim_df.columns:
            return pd.DataFrame()
        top = self.sim_df[meal_id].drop(meal_id).nlargest(n)
        df  = self.plats[self.plats["meal_id"].isin(top.index)].copy()
        df["similarite"] = df["meal_id"].map(top.to_dict())
        return df.sort_values("similarite", ascending=False)
