import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles import inject
from recommender import Recommender

st.set_page_config(page_title="Vos recommandations", layout="wide", initial_sidebar_state="collapsed")

st.markdown(inject("""
.block-container { padding: 40px 48px 80px !important; max-width: 1100px !important; }

.page-title { font-family:'DM Serif Display',serif; font-size:28px; font-weight:400; color:#1a1a1a; margin-bottom:6px; }
.page-sub   { font-size:13px; color:#aaa; margin-bottom:36px; }

.profil-bar { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:36px; }
.chip { font-size:12px; padding:4px 12px; border-radius:20px; border:0.5px solid #e8e8e0; color:#666; background:#fff; }
.chip.accent  { background:#f7f6f3; border-color:#ddd; color:#1a1a1a; font-weight:500; }
.chip.allergy { background:#FCEBEB; border-color:#F09595; color:#791F1F; }

.sec-label {
    font-size:10px; letter-spacing:0.12em; text-transform:uppercase;
    color:#bbb; padding-bottom:10px; border-bottom:0.5px solid #f0f0ee; margin-bottom:18px;
}

/* Carte plat résultat */
.plat-card {
    padding: 18px 20px;
    border: 0.5px solid #e8e8e0;
    border-radius: 10px;
    margin-bottom: 10px;
    background: #fff;
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.plat-card:hover { border-color: #bbb; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.plat-card.selected { border-color: #1a1a1a; box-shadow: 0 2px 16px rgba(0,0,0,0.08); }

.plat-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }
.plat-nom    { font-family:'DM Serif Display',serif; font-size:16px; color:#1a1a1a; }
.plat-badge  { font-size:11px; font-weight:500; color:#085041; background:#E1F5EE; padding:3px 9px; border-radius:20px; }

.plat-tags   { display:flex; gap:5px; flex-wrap:wrap; margin-bottom:10px; }
.ptag        { font-size:11px; padding:2px 9px; border-radius:3px; border:0.5px solid #e8e8e0; color:#888; background:#fafafa; }
.ptag.alg    { background:#FCEBEB; border-color:#F09595; color:#791F1F; }
.ptag.p1     { background:#FAEEDA; border-color:#EF9F27; color:#633806; }
.ptag.p2     { background:#FAEEDA; border-color:#E88B14; color:#5a3002; }
.ptag.p3     { background:#FCEBEB; border-color:#E24B4A; color:#791F1F; }
.ptag.saison { background:#EEEDFE; border-color:#A09BDB; color:#3C3489; }

.plat-footer { display:flex; justify-content:space-between; align-items:center; }
.note-own    { font-size:11px; color:#F5A623; }
.restos-hint { font-size:11px; color:#534AB7; cursor:pointer; }

/* Restaurant card */
.resto-card  { padding:14px 16px; border:0.5px solid #e8e8e0; border-radius:8px; margin-bottom:8px; background:#fff; }
.resto-nom   { font-size:14px; font-weight:500; color:#1a1a1a; margin-bottom:3px; }
.resto-meta  { font-size:11px; color:#bbb; margin-bottom:8px; }
.resto-row   { display:flex; justify-content:space-between; align-items:center; }
.dist-badge  { font-size:11px; color:#534AB7; background:#EEEDFE; padding:2px 9px; border-radius:20px; }
.etoiles     { font-size:12px; color:#BA7517; }

/* Stars inline résultats */
.stars-inline { display:flex; gap:3px; margin-top:6px; }
.s { font-size:18px; color:#e0e0da; cursor:pointer; transition:color 0.1s; }
.s.on { color:#F5A623; }
"""), unsafe_allow_html=True)

# ── Vérification session ─────────────────────────────────
if "mm_profil" not in st.session_state:
    st.switch_page("accueil.py")

profil    = st.session_state["mm_profil"]
notes_usr = st.session_state.get("mm_notes", {})
candidats = st.session_state.get("mm_candidats", [])

# ── Chargement modèle ────────────────────────────────────
@st.cache_resource
def load_rec():
    return Recommender(
        data_dir=os.path.join(os.path.dirname(__file__), "..")
    ).fit()

@st.cache_data
def load_restos():
    return pd.read_csv(os.path.join(os.path.dirname(__file__), "../restaurants.csv"))

rec    = load_rec()
restos = load_restos()

# ── Géocodage ────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def geocode(ville: str):
    FALLBACK = {
        "cotonou":  (6.365,  2.419), "dakar":    (14.693, -17.448),
        "abidjan":  (5.354,  -4.002),"lomé":     (6.130,   1.223),
        "accra":    (5.603,  -0.187),"paris":    (48.856,  2.352),
        "lyon":     (45.748,  4.847),"marseille":(43.296,  5.381),
    }
    key = ville.lower().split(",")[0].strip()
    if key in FALLBACK:
        return FALLBACK[key]
    try:
        from geopy.geocoders import Nominatim
        g = Nominatim(user_agent="mealmatch_app", timeout=5)
        loc = g.geocode(ville)
        if loc:
            return loc.latitude, loc.longitude
    except Exception:
        pass
    return (6.365, 2.419)

user_lat, user_lon = geocode(profil["ville"])

# ── Calcul recommandations finales ───────────────────────
# Si l'utilisateur a noté des plats → affiner avec les notes
notes_series = {int(k): v for k, v in notes_usr.items() if v > 0}

recs = rec.recommander(
    cuisine_pref = profil["cuisine"],
    allergies    = profil["allergies"],
    piment_max   = profil["piment"],
    saison       = profil["saison"],
    notes_user   = notes_series,
    n            = 8,
) if notes_series else rec.recommander(
    cuisine_pref = profil["cuisine"],
    allergies    = profil["allergies"],
    piment_max   = profil["piment"],
    saison       = profil["saison"],
    n            = 8,
)

# ── Restaurants proches ──────────────────────────────────
def restos_proches(meal_id: int, n: int = 5):
    df = restos[restos["plats"].apply(
        lambda x: str(meal_id) in str(x).split("|")
    )].copy()
    if df.empty:
        row = rec.plats[rec.plats["meal_id"] == meal_id]
        if not row.empty:
            df = restos[restos["cuisine"] == row["cuisine"].values[0]].copy()
    if df.empty:
        return pd.DataFrame()
    df["dist"] = df.apply(
        lambda r: round(geodesic((user_lat, user_lon), (r["latitude"], r["longitude"])).km, 1), axis=1
    )
    return df.sort_values("dist").head(n)

# ── État sélection plat ──────────────────────────────────
if "mm_selected_meal" not in st.session_state:
    st.session_state["mm_selected_meal"] = None
if "mm_result_notes" not in st.session_state:
    st.session_state["mm_result_notes"] = {}

# ══════════════════════════════════════════════════════════
# AFFICHAGE
# ══════════════════════════════════════════════════════════
if st.button("← Modifier mes notes", key="btn_back"):
    st.switch_page("pages/2_notation.py")

st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
st.markdown(f'<div class="page-title">Vos recommandations, {profil["prenom"]}</div>', unsafe_allow_html=True)

n_notes_faites = len(notes_series)
if n_notes_faites > 0:
    st.markdown(f'<div class="page-sub">Affinées grâce à vos {n_notes_faites} notes · {profil["ville"]}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="page-sub">Basées sur votre profil · {profil["ville"]}</div>', unsafe_allow_html=True)

# Chips profil
PIMENT_L = {0:"sans piment", 1:"piment léger", 2:"piment moyen", 3:"piment fort"}
chips = [
    f'<span class="chip accent">{profil["cuisine"].capitalize()}</span>',
    f'<span class="chip">{PIMENT_L[profil["piment"]]}</span>',
    f'<span class="chip">{profil["saison"].capitalize()}</span>',
] + [f'<span class="chip allergy">{a}</span>' for a in profil["allergies"]]
st.markdown(f'<div class="profil-bar">{"".join(chips)}</div>', unsafe_allow_html=True)

if recs.empty:
    st.info("Aucun plat trouvé. Revenez au formulaire et assouplissez vos critères.")
    st.stop()

# ── Deux colonnes ────────────────────────────────────────
col_plats, col_detail = st.columns([3, 2], gap="large")

PIMENT_FIRE = {0:"", 1:"piment léger", 2:"piment", 3:"piment fort"}
PIMENT_CLS  = {0:"", 1:"p1", 2:"p2", 3:"p3"}
NOTE_LABEL  = {1:"Pas aimé", 2:"Bof", 3:"Correct", 4:"Bon", 5:"Excellent"}

selected = st.session_state["mm_selected_meal"]

with col_plats:
    st.markdown('<div class="sec-label">Plats recommandés — cliquez pour voir les restaurants</div>', unsafe_allow_html=True)

    for _, row in recs.iterrows():
        mid      = int(row["meal_id"])
        alg      = str(row.get("allergenes",""))
        alg_list = [a.strip() for a in alg.split("|") if a.strip()]
        piment_v = int(row["piment"])
        saison_v = str(row["saison"])
        score    = float(row.get("score", 0))
        note_act = st.session_state["mm_result_notes"].get(mid, 0)
        is_sel   = (selected == mid)

        alg_tags    = "".join([f'<span class="ptag alg">{a}</span>' for a in alg_list])
        piment_tag  = f'<span class="ptag {PIMENT_CLS[piment_v]}">{PIMENT_FIRE[piment_v]}</span>' if piment_v > 0 else ""
        saison_tag  = f'<span class="ptag saison">{saison_v}</span>' if saison_v != "toutes" else ""
        cuisine_tag = f'<span class="ptag">{str(row["cuisine"]).capitalize()}</span>'
        note_stars  = ("★" * note_act + "☆" * (5 - note_act)) if note_act > 0 else ""
        note_html   = f'<span class="note-own">{note_stars} {NOTE_LABEL[note_act]}</span>' if note_act > 0 else '<span style="font-size:11px;color:#ddd;">non noté</span>'
        selected_cls = "selected" if is_sel else ""

        st.markdown(f"""
        <div class="plat-card {selected_cls}" id="card_{mid}">
            <div class="plat-header">
                <div class="plat-nom">{row['nom']}</div>
                <span class="plat-badge">{score:.1f}</span>
            </div>
            <div class="plat-tags">{cuisine_tag}{piment_tag}{saison_tag}{alg_tags}</div>
            <div class="plat-footer">
                {note_html}
                <span class="restos-hint">{'Restaurants selectionnes' if is_sel else 'Voir les restaurants →'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Boutons action : sélectionner + noter
        ba, bb, bc, bd, be, bf = st.columns([2, 1, 1, 1, 1, 1])
        with ba:
            label_sel = "Restaurants selectionnes" if is_sel else "Voir les restaurants"
            if st.button(label_sel, key=f"sel_{mid}", use_container_width=True):
                st.session_state["mm_selected_meal"] = mid if not is_sel else None
                st.rerun()

        for star_i, col in enumerate([bb, bc, bd, be, bf], start=1):
            with col:
                star_char = "★" if note_act >= star_i else "☆"
                if col.button(star_char, key=f"rstar_{mid}_{star_i}", help=NOTE_LABEL[star_i]):
                    if st.session_state["mm_result_notes"].get(mid) == star_i:
                        st.session_state["mm_result_notes"][mid] = 0
                    else:
                        st.session_state["mm_result_notes"][mid] = star_i
                    st.rerun()

        st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)

# ── Colonne droite : restaurants ─────────────────────────
with col_detail:
    if selected:
        plat_row = rec.plats[rec.plats["meal_id"] == selected]
        plat_nom = plat_row["nom"].values[0] if not plat_row.empty else "ce plat"

        st.markdown(f'<div class="sec-label">Restaurants · {plat_nom}</div>', unsafe_allow_html=True)

        r_df = restos_proches(selected, n=6)

        if not r_df.empty:
            # Carte
            center_lat = (user_lat + r_df["latitude"].mean()) / 2
            center_lon = (user_lon + r_df["longitude"].mean()) / 2
            zoom = 13 if r_df["dist"].max() < 15 else 6

            m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="CartoDB positron")

            folium.CircleMarker(
                [user_lat, user_lon], radius=7,
                color="#1a1a1a", fill=True, fill_color="#1a1a1a",
                fill_opacity=1, tooltip="Vous"
            ).add_to(m)

            for _, r in r_df.iterrows():
                prix_s = "€" * int(r.get("prix", 1))
                folium.CircleMarker(
                    [r["latitude"], r["longitude"]], radius=7,
                    color="#534AB7", fill=True, fill_color="#534AB7",
                    fill_opacity=0.85,
                    tooltip=f"{r['nom']} — {r['dist']} km",
                    popup=folium.Popup(
                        f"<b>{r['nom']}</b><br>{r['cuisine'].capitalize()} · {prix_s}<br>"
                        f"{'★' * int(r['note'])} {r['note']}<br>{r['dist']} km",
                        max_width=180
                    )
                ).add_to(m)

            st_folium(m, height=260, use_container_width=True)
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

            # Liste restaurants
            for _, r in r_df.iterrows():
                prix_s   = "€" * int(r.get("prix", 1))
                etoiles  = "★" * int(r["note"]) + "☆" * (5 - int(r["note"]))
                st.markdown(f"""
                <div class="resto-card">
                    <div class="resto-nom">{r['nom']}</div>
                    <div class="resto-meta">{r['cuisine'].capitalize()} · {r['ville']}</div>
                    <div class="resto-row">
                        <div>
                            <span class="etoiles">{etoiles}</span>
                            <span style="font-size:11px;color:#bbb;"> {r['note']}</span>
                            <span style="font-size:11px;color:#ccc;margin-left:6px;">{prix_s}</span>
                        </div>
                        <span class="dist-badge">{r['dist']} km</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"Aucun restaurant trouvé à proximité pour « {plat_nom} ».")

    else:
        # État vide — invitation à sélectionner
        st.markdown("""
        <div style="border:0.5px solid #f0f0ee; border-radius:10px; padding:40px 24px; text-align:center; margin-top:40px;">
            <div style="font-family:'DM Serif Display',serif; font-size:18px; color:#1a1a1a; margin-bottom:10px;">Sélectionnez un plat</div>
            <div style="font-size:13px; color:#bbb; line-height:1.7;">
                Cliquez sur "Voir les restaurants" sous un plat<br>pour afficher la carte et la liste des<br>restaurants les plus proches.
            </div>
        </div>
        """, unsafe_allow_html=True)

# Style boutons étoiles résultats
st.markdown("""
<style>
div[data-testid="stButton"] button {
    background: none !important;
    border: none !important;
    box-shadow: none !important;
    min-height: 0 !important;
    height: auto !important;
    padding: 2px 4px !important;
    font-size: 18px !important;
    color: #e0e0da !important;
}
div[data-testid="stButton"] button:hover {
    color: #F5A623 !important;
    background: none !important;
    border: none !important;
    transform: scale(1.2);
}
</style>
""", unsafe_allow_html=True)
