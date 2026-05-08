import streamlit as st
import pandas as pd
import time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles import inject
from recommender import Recommender
from localisation import restaurants_locaux, plats_disponibles_localement
from geopy.geocoders import Nominatim

st.set_page_config(page_title="MealMatch", layout="centered", initial_sidebar_state="collapsed")
st.markdown(inject("""
.block-container { max-width:480px !important; padding:80px 24px !important; }
.load-title { font-family:'DM Serif Display',serif; font-size:26px; font-weight:400;
              color:#1a1a1a; margin-bottom:10px; text-align:center; }
.load-sub   { font-size:13px; color:#bbb; text-align:center; margin-bottom:48px; line-height:1.7; }
.step-line  { display:flex; align-items:center; gap:12px; padding:12px 0;
              border-bottom:0.5px solid #f5f5f3; }
.step-icon  { width:28px; height:28px; border-radius:50%; display:flex;
              align-items:center; justify-content:center; font-size:12px; flex-shrink:0; }
.step-done  { background:#E1F5EE; color:#085041; }
.step-wait  { background:#f5f5f3; color:#ccc; }
.step-active{ background:#EEEDFE; color:#534AB7; }
.step-text  { font-size:13px; color:#1a1a1a; }
.step-sub   { font-size:11px; color:#bbb; }
.prog-bar   { height:3px; background:#f0f0ee; border-radius:2px; margin:32px 0 16px; overflow:hidden; }
.prog-fill  { height:100%; background:#1a1a1a; border-radius:2px; transition:width 0.4s ease; }
"""), unsafe_allow_html=True)

if "mm_profil" not in st.session_state:
    st.switch_page("accueil.py")

profil = st.session_state["mm_profil"]
st.markdown(f'<div class="load-title">Bonjour, {profil["prenom"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="load-sub">Nous recherchons les plats disponibles<br>à <b>{profil["ville"]}</b> selon votre profil.</div>', unsafe_allow_html=True)

prog_box  = st.empty()
steps_box = st.empty()

STEPS = [
    ("Localisation de votre ville",      f'Recherche des restaurants à {profil["ville"]}'),
    ("Plats disponibles localement",     "Uniquement ce que vous pouvez trouver ici"),
    ("Filtrage selon votre profil",      "Piment, allergies, saison"),
    ("Sélection des plats à découvrir",  "10 plats représentatifs à noter"),
]

def render(current, pct):
    prog_box.markdown(f"""
    <div class="prog-bar"><div class="prog-fill" style="width:{pct}%;"></div></div>
    <div style="text-align:right;font-size:11px;color:#bbb;margin-top:4px;">{pct}%</div>
    """, unsafe_allow_html=True)
    html = ""
    for i, (titre, sous) in enumerate(STEPS):
        if i < current:    cls, ic = "step-done",  "✓"
        elif i == current: cls, ic = "step-active", "…"
        else:              cls, ic = "step-wait",   str(i+1)
        html += f'<div class="step-line"><div class="step-icon {cls}">{ic}</div><div><div class="step-text">{titre}</div><div class="step-sub">{sous}</div></div></div>'
    steps_box.markdown(html, unsafe_allow_html=True)

# ── Étape 1 : Géocodage ──────────────────────────────────
render(0, 10)

FALLBACK = {
    "cotonou":(6.365,2.419),"dakar":(14.693,-17.448),
    "abidjan":(5.354,-4.002),"lomé":(6.130,1.223),
    "accra":(5.603,-0.187),"paris":(48.856,2.352),
    "lyon":(45.748,4.847),"marseille":(43.296,5.381),
}
key = profil["ville"].lower().strip().split(",")[0].strip()
if key in FALLBACK:
    user_lat, user_lon = FALLBACK[key]
else:
    try:
        geo = Nominatim(user_agent="mealmatch", timeout=5)
        loc = geo.geocode(profil["ville"])
        user_lat, user_lon = (loc.latitude, loc.longitude) if loc else (6.365, 2.419)
    except:
        user_lat, user_lon = 6.365, 2.419

st.session_state["mm_coords"] = (user_lat, user_lon)
time.sleep(0.6)

# ── Étape 2 : Restaurants locaux ─────────────────────────
render(1, 35)

@st.cache_resource
def load_rec():
    return Recommender(data_dir=os.path.join(os.path.dirname(__file__), "..")).fit()

@st.cache_data
def load_restos():
    return pd.read_csv(os.path.join(os.path.dirname(__file__), "../restaurants.csv"))

rec    = load_rec()
restos = load_restos()

restos_loc  = restaurants_locaux(restos, profil["ville"], user_lat, user_lon)
meal_ids_loc = plats_disponibles_localement(restos_loc)

# Sauvegarder pour les pages suivantes
st.session_state["mm_restos_locaux"] = restos_loc.to_dict("records")
st.session_state["mm_meal_ids_locaux"] = meal_ids_loc

n_restos = len(restos_loc)
n_plats  = len(meal_ids_loc)
time.sleep(0.6)

# ── Étape 3 : Filtrage profil ─────────────────────────────
render(2, 65)

STEPS[1] = (STEPS[1][0], f"{n_restos} restaurants · {n_plats} plats trouvés à {profil['ville']}")
time.sleep(0.6)

# ── Étape 4 : Candidats à noter ───────────────────────────
render(3, 85)

candidats = rec.candidats_a_noter(
    cuisine_pref   = profil["cuisine"],
    allergies      = profil["allergies"],
    piment_max     = profil["piment"],
    saison         = profil["saison"],
    meal_ids_locaux= meal_ids_loc,
    n              = 10,
)

# Si pas assez de plats locaux → élargir sans filtre local
if len(candidats) < 5:
    candidats = rec.candidats_a_noter(
        cuisine_pref = profil["cuisine"],
        allergies    = profil["allergies"],
        piment_max   = profil["piment"],
        saison       = profil["saison"],
        n            = 10,
    )
    st.session_state["mm_local_warning"] = f"Peu de restaurants trouvés à {profil['ville']} — nous avons élargi la sélection."
else:
    st.session_state.pop("mm_local_warning", None)

st.session_state["mm_candidats"] = candidats.to_dict("records")
st.session_state["mm_notes"]     = {}

render(len(STEPS), 100)
time.sleep(0.3)
st.switch_page("pages/2_notation.py")
