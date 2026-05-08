import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles import inject
from recommender import Recommender

st.set_page_config(page_title="Vos recommandations", layout="wide", initial_sidebar_state="collapsed")
st.markdown(inject("""
.block-container { padding:40px 48px 80px !important; max-width:1100px !important; }
.page-title { font-family:'DM Serif Display',serif; font-size:28px; font-weight:400; color:#1a1a1a; margin-bottom:6px; }
.page-sub   { font-size:13px; color:#aaa; margin-bottom:12px; }
.local-info { font-size:12px; color:#085041; background:#E1F5EE; padding:8px 14px;
              border-radius:6px; margin-bottom:28px; display:inline-block; }
.local-warn { font-size:12px; color:#633806; background:#FAEEDA; padding:8px 14px;
              border-radius:6px; margin-bottom:28px; display:inline-block; }
.profil-bar { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:32px; }
.chip       { font-size:12px; padding:4px 12px; border-radius:20px; border:0.5px solid #e8e8e0; color:#666; }
.chip.accent{ background:#f7f6f3; border-color:#ddd; color:#1a1a1a; font-weight:500; }
.chip.allergy{ background:#FCEBEB; border-color:#F09595; color:#791F1F; }
.sec-label  { font-size:10px; letter-spacing:0.12em; text-transform:uppercase; color:#bbb;
              padding-bottom:10px; border-bottom:0.5px solid #f0f0ee; margin-bottom:18px; }
.plat-card  { padding:18px 20px; border:0.5px solid #e8e8e0; border-radius:10px;
              margin-bottom:10px; background:#fff; transition:border-color 0.15s; }
.plat-card:hover { border-color:#bbb; }
.plat-card.selected { border-color:#1a1a1a; }
.plat-header{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }
.plat-nom   { font-family:'DM Serif Display',serif; font-size:16px; color:#1a1a1a; }
.plat-badge { font-size:11px; font-weight:500; color:#085041; background:#E1F5EE; padding:3px 9px; border-radius:20px; }
.plat-tags  { display:flex; gap:5px; flex-wrap:wrap; margin-bottom:10px; }
.ptag       { font-size:11px; padding:2px 9px; border-radius:3px; border:0.5px solid #e8e8e0; color:#888; background:#fafafa; }
.ptag.alg   { background:#FCEBEB; border-color:#F09595; color:#791F1F; }
.ptag.p1    { background:#FAEEDA; border-color:#EF9F27; color:#633806; }
.ptag.p2    { background:#FAEEDA; border-color:#E88B14; color:#5a3002; }
.ptag.p3    { background:#FCEBEB; border-color:#E24B4A; color:#791F1F; }
.ptag.saison{ background:#EEEDFE; border-color:#A09BDB; color:#3C3489; }
.plat-footer{ display:flex; justify-content:space-between; align-items:center; }
.note-own   { font-size:11px; color:#F5A623; }
.resto-card { padding:14px 16px; border:0.5px solid #e8e8e0; border-radius:8px; margin-bottom:8px; background:#fff; }
.resto-nom  { font-size:14px; font-weight:500; color:#1a1a1a; margin-bottom:3px; }
.resto-meta { font-size:11px; color:#bbb; margin-bottom:8px; }
.resto-row  { display:flex; justify-content:space-between; align-items:center; }
.dist-badge { font-size:11px; color:#534AB7; background:#EEEDFE; padding:2px 9px; border-radius:20px; }
.etoiles    { font-size:12px; color:#BA7517; }
div[data-testid="stButton"] button {
    background:none !important; border:none !important; box-shadow:none !important;
    min-height:0 !important; height:auto !important; padding:2px 4px !important;
    font-size:18px !important; color:#e0e0da !important;
}
div[data-testid="stButton"] button:hover {
    color:#F5A623 !important; background:none !important; border:none !important;
}
"""), unsafe_allow_html=True)

if "mm_profil" not in st.session_state:
    st.switch_page("accueil.py")

profil       = st.session_state["mm_profil"]
notes_usr    = st.session_state.get("mm_notes", {})
notes_series = {int(k): v for k, v in notes_usr.items() if v > 0}
meal_ids_loc = st.session_state.get("mm_meal_ids_locaux", None)
restos_loc_r = st.session_state.get("mm_restos_locaux", [])
restos_locaux= pd.DataFrame(restos_loc_r) if restos_loc_r else pd.DataFrame()
user_lat, user_lon = st.session_state.get("mm_coords", (6.365, 2.419))
local_warn   = st.session_state.get("mm_local_warning", None)

@st.cache_resource
def load_rec():
    return Recommender(data_dir=os.path.join(os.path.dirname(__file__), "..")).fit()

rec = load_rec()

# Recommandations avec filtre local
recs = rec.recommander(
    cuisine_pref   = profil["cuisine"],
    allergies      = profil["allergies"],
    piment_max     = profil["piment"],
    saison         = profil["saison"],
    notes_user     = notes_series if notes_series else None,
    meal_ids_locaux= meal_ids_loc,
    n              = 8,
)

# Restaurants pour un plat donné — uniquement locaux
def restos_du_plat(meal_id: int):
    if restos_locaux.empty:
        return pd.DataFrame()
    df = restos_locaux[restos_locaux["plats"].apply(
        lambda x: str(meal_id) in str(x).split("|")
    )].copy()
    if df.empty:
        # fallback : même cuisine dans les restos locaux
        row = rec.plats[rec.plats["meal_id"] == meal_id]
        if not row.empty:
            df = restos_locaux[restos_locaux["cuisine"] == row["cuisine"].values[0]].copy()
    if df.empty:
        return pd.DataFrame()
    df["dist"] = df.apply(
        lambda r: round(geodesic((user_lat, user_lon), (r["latitude"], r["longitude"])).km, 1), axis=1
    )
    return df.sort_values("dist")

# État UI
if "mm_selected_meal" not in st.session_state:
    st.session_state["mm_selected_meal"] = None
if "mm_result_notes" not in st.session_state:
    st.session_state["mm_result_notes"]  = {}

# ── Header ───────────────────────────────────────────────
if st.button("← Modifier mes notes", key="btn_back"):
    st.switch_page("pages/2_notation.py")

st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
st.markdown(f'<div class="page-title">Vos recommandations, {profil["prenom"]}</div>', unsafe_allow_html=True)

n_restos_loc = len(restos_locaux) if not restos_locaux.empty else 0
n_plats_loc  = len(meal_ids_loc)  if meal_ids_loc else 0

if local_warn:
    st.markdown(f'<div class="local-warn">{local_warn}</div>', unsafe_allow_html=True)
else:
    st.markdown(
        f'<div class="local-info">{n_restos_loc} restaurants · {n_plats_loc} plats disponibles à {profil["ville"]}</div>',
        unsafe_allow_html=True
    )

n_notes = len(notes_series)
st.markdown(
    f'<div class="page-sub">{"Affinées grâce à vos " + str(n_notes) + " notes" if n_notes else "Basées sur votre profil"} · {profil["ville"]}</div>',
    unsafe_allow_html=True
)

PIMENT_L = {0:"sans piment", 1:"piment léger", 2:"piment moyen", 3:"piment fort"}
chips = [
    f'<span class="chip accent">{profil["cuisine"].capitalize()}</span>',
    f'<span class="chip">{PIMENT_L[profil["piment"]]}</span>',
    f'<span class="chip">{profil["saison"].capitalize()}</span>',
] + [f'<span class="chip allergy">{a}</span>' for a in profil["allergies"]]
st.markdown(f'<div class="profil-bar">{"".join(chips)}</div>', unsafe_allow_html=True)

if recs.empty:
    st.info("Aucun plat trouvé à votre emplacement avec ces critères. Revenez au formulaire.")
    st.stop()

# ── Layout ───────────────────────────────────────────────
col_plats, col_detail = st.columns([3, 2], gap="large")
PIMENT_FIRE = {0:"", 1:"piment léger", 2:"piment", 3:"piment fort"}
PIMENT_CLS  = {0:"", 1:"p1", 2:"p2", 3:"p3"}
NOTE_LABEL  = {1:"Pas aimé", 2:"Bof", 3:"Correct", 4:"Bon", 5:"Excellent"}
selected    = st.session_state["mm_selected_meal"]

with col_plats:
    st.markdown('<div class="sec-label">Plats disponibles à votre emplacement</div>', unsafe_allow_html=True)

    for _, row in recs.iterrows():
        mid      = int(row["meal_id"])
        alg      = str(row.get("allergenes",""))
        alg_list = [a.strip() for a in alg.split("|") if a.strip()]
        piment_v = int(row["piment"])
        saison_v = str(row["saison"])
        score    = float(row.get("score", 0))
        note_act = st.session_state["mm_result_notes"].get(mid, 0)
        is_sel   = (selected == mid)

        alg_tags   = "".join([f'<span class="ptag alg">{a}</span>' for a in alg_list])
        piment_tag = f'<span class="ptag {PIMENT_CLS[piment_v]}">{PIMENT_FIRE[piment_v]}</span>' if piment_v > 0 else ""
        saison_tag = f'<span class="ptag saison">{saison_v}</span>' if saison_v != "toutes" else ""
        cuisine_tag= f'<span class="ptag">{str(row["cuisine"]).capitalize()}</span>'
        note_html  = f'<span class="note-own">{"★"*note_act+"☆"*(5-note_act)} {NOTE_LABEL[note_act]}</span>' if note_act > 0 else '<span style="font-size:11px;color:#ddd;">non noté</span>'
        sel_cls    = "selected" if is_sel else ""

        st.markdown(f"""
        <div class="plat-card {sel_cls}">
            <div class="plat-header">
                <div class="plat-nom">{row['nom']}</div>
                <span class="plat-badge">{score:.1f}</span>
            </div>
            <div class="plat-tags">{cuisine_tag}{piment_tag}{saison_tag}{alg_tags}</div>
            <div class="plat-footer">{note_html}
                <span style="font-size:11px;color:{'#1a1a1a' if is_sel else '#534AB7'};">
                    {"Restaurants affichés" if is_sel else "Voir les restaurants →"}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        ba, bb, bc, bd, be, bf = st.columns([2, 1, 1, 1, 1, 1])
        with ba:
            if st.button("Voir les restaurants" if not is_sel else "Fermer",
                         key=f"sel_{mid}", use_container_width=True):
                st.session_state["mm_selected_meal"] = mid if not is_sel else None
                st.rerun()
        for star_i, col in enumerate([bb, bc, bd, be, bf], start=1):
            with col:
                char = "★" if note_act >= star_i else "☆"
                if col.button(char, key=f"rstar_{mid}_{star_i}", help=NOTE_LABEL[star_i]):
                    st.session_state["mm_result_notes"][mid] = 0 if st.session_state["mm_result_notes"].get(mid) == star_i else star_i
                    st.rerun()
        st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)

with col_detail:
    if selected:
        plat_nom = rec.plats[rec.plats["meal_id"] == selected]["nom"].values
        plat_nom = plat_nom[0] if len(plat_nom) else "ce plat"
        st.markdown(f'<div class="sec-label">Restaurants à {profil["ville"]} · {plat_nom}</div>', unsafe_allow_html=True)

        r_df = restos_du_plat(selected)

        if not r_df.empty:
            m = folium.Map(
                location=[(user_lat + r_df["latitude"].mean())/2,
                           (user_lon + r_df["longitude"].mean())/2],
                zoom_start=13 if r_df["dist"].max() < 15 else 7,
                tiles="CartoDB positron"
            )
            folium.CircleMarker([user_lat, user_lon], radius=7,
                color="#1a1a1a", fill=True, fill_color="#1a1a1a",
                fill_opacity=1, tooltip="Vous").add_to(m)

            for _, r in r_df.iterrows():
                prix_s = "€" * int(r.get("prix", 1))
                folium.CircleMarker(
                    [r["latitude"], r["longitude"]], radius=7,
                    color="#534AB7", fill=True, fill_color="#534AB7", fill_opacity=0.85,
                    tooltip=f"{r['nom']} — {r['dist']} km",
                    popup=folium.Popup(
                        f"<b>{r['nom']}</b><br>{r['cuisine'].capitalize()} · {prix_s}<br>"
                        f"{'★'*int(r['note'])} {r['note']}<br>{r['dist']} km de vous",
                        max_width=180)
                ).add_to(m)

            st_folium(m, height=260, use_container_width=True)
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

            for _, r in r_df.iterrows():
                prix_s  = "€" * int(r.get("prix",1))
                etoiles = "★"*int(r["note"]) + "☆"*(5-int(r["note"]))
                st.markdown(f"""
                <div class="resto-card">
                    <div class="resto-nom">{r['nom']}</div>
                    <div class="resto-meta">{r['cuisine'].capitalize()} · {r['ville']}</div>
                    <div class="resto-row">
                        <div><span class="etoiles">{etoiles}</span>
                             <span style="font-size:11px;color:#bbb;"> {r['note']}</span>
                             <span style="font-size:11px;color:#ccc;margin-left:6px;">{prix_s}</span>
                        </div>
                        <span class="dist-badge">{r['dist']} km</span>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info(f"Aucun restaurant trouvé à {profil['ville']} pour ce plat.")
    else:
        st.markdown("""
        <div style="border:0.5px solid #f0f0ee;border-radius:10px;padding:40px 24px;text-align:center;margin-top:40px;">
            <div style="font-family:'DM Serif Display',serif;font-size:18px;color:#1a1a1a;margin-bottom:10px;">Sélectionnez un plat</div>
            <div style="font-size:13px;color:#bbb;line-height:1.7;">
                Cliquez sur "Voir les restaurants"<br>pour afficher les restaurants<br>disponibles à votre emplacement.
            </div>
        </div>""", unsafe_allow_html=True)
