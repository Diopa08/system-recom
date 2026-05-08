"""
Logique de localisation :
1. Trouver les restaurants dans la ville (ou région proche)
2. Déduire les plats disponibles localement
3. Ne recommander que ces plats
"""
import pandas as pd
from geopy.distance import geodesic

# Correspondances ville → région / pays
# Permet d'élargir la recherche si pas assez de restaurants dans la ville exacte
REGION_MAP = {
    # Bénin
    "cotonou"       : ["cotonou"],
    "porto-novo"    : ["cotonou", "porto-novo"],
    "abomey"        : ["cotonou"],
    # Sénégal
    "dakar"         : ["dakar"],
    "saint-louis"   : ["dakar"],
    # Côte d'Ivoire
    "abidjan"       : ["abidjan"],
    "yamoussoukro"  : ["abidjan"],
    # Togo
    "lomé"          : ["lomé"],
    # Ghana
    "accra"         : ["accra"],
    # France
    "paris"         : ["paris"],
    "lyon"          : ["lyon", "paris"],
    "marseille"     : ["marseille", "paris"],
    "bordeaux"      : ["paris"],
    "toulouse"      : ["paris"],
    "nice"          : ["paris"],
}

def normaliser_ville(ville: str) -> str:
    return ville.lower().strip().split(",")[0].strip()

def villes_recherche(ville: str) -> list:
    """Retourne la liste des villes à chercher (ville + région élargie)."""
    key = normaliser_ville(ville)
    return REGION_MAP.get(key, [key])

def restaurants_locaux(restos_df: pd.DataFrame, ville: str,
                       user_lat: float, user_lon: float,
                       rayon_km: float = 50) -> pd.DataFrame:
    """
    Retourne les restaurants disponibles pour une ville donnée.
    Stratégie en cascade :
      1. Restaurants dans les villes mappées à la région
      2. Si < 3 résultats → élargir par distance GPS (rayon_km)
      3. Si toujours vide → retourner tous les restaurants
         de la même cuisine (dernier recours)
    """
    villes = villes_recherche(ville)

    # Étape 1 : filtre par ville
    df = restos_df[restos_df["ville"].str.lower().isin(villes)].copy()

    # Étape 2 : élargir par distance si pas assez
    if len(df) < 3:
        restos_df2 = restos_df.copy()
        restos_df2["dist_km"] = restos_df2.apply(
            lambda r: geodesic((user_lat, user_lon), (r["latitude"], r["longitude"])).km,
            axis=1
        )
        df = restos_df2[restos_df2["dist_km"] <= rayon_km].copy()

    return df

def plats_disponibles_localement(restos_locaux: pd.DataFrame) -> set:
    """
    Retourne l'ensemble des meal_ids disponibles dans les restaurants locaux.
    """
    meal_ids = set()
    for plats_str in restos_locaux["plats"].dropna():
        for mid in str(plats_str).split("|"):
            mid = mid.strip()
            if mid.isdigit():
                meal_ids.add(int(mid))
    return meal_ids
