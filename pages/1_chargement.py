import streamlit as st
import time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles import inject
from recommender import Recommender

st.set_page_config(page_title="MealMatch", layout="centered", initial_sidebar_state="collapsed")

st.markdown(inject("""
.block-container { max-width: 480px !important; padding: 80px 24px !important; }
.load-title { font-family:'DM Serif Display',serif; font-size:26px; font-weight:400; color:#1a1a1a; margin-bottom:10px; text-align:center; }
.load-sub   { font-size:13px; color:#bbb; text-align:center; margin-bottom:48px; line-height:1.7; }
.step-line  { display:flex; align-items:center; gap:12px; padding:12px 0; border-bottom:0.5px solid #f5f5f3; }
.step-icon  { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; flex-shrink:0; }
.step-done  { background:#E1F5EE; color:#085041; }
.step-wait  { background:#f5f5f3; color:#ccc; }
.step-active{ background:#EEEDFE; color:#534AB7; }
.step-text  { font-size:13px; color:#1a1a1a; }
.step-sub   { font-size:11px; color:#bbb; }

/* Barre de progression custom */
.prog-bar { height:3px; background:#f0f0ee; border-radius:2px; margin: 32px 0 16px; overflow:hidden; }
.prog-fill { height:100%; background:#1a1a1a; border-radius:2px; transition:width 0.4s ease; }
"""), unsafe_allow_html=True)

# Vérification session
if "mm_profil" not in st.session_state:
    st.switch_page("accueil.py")

profil = st.session_state["mm_profil"]

st.markdown(f'<div class="load-title">Bonjour, {profil["prenom"]}</div>', unsafe_allow_html=True)
st.markdown('<div class="load-sub">Nous analysons vos préférences et préparons<br>une sélection de plats à découvrir.</div>', unsafe_allow_html=True)

# Conteneurs dynamiques
prog_bar  = st.empty()
steps_box = st.empty()

STEPS = [
    ("Analyse de votre profil",          "Cuisine, piment, saison, allergies"),
    ("Filtrage des plats compatibles",   "Exclusion des allergènes et restrictions"),
    ("Calcul des scores de popularité",  "Collaborative filtering item-item"),
    ("Sélection des candidats",          "10 plats représentatifs à découvrir"),
]

def render(current: int, pct: int):
    prog_bar.markdown(f"""
    <div class="prog-bar">
        <div class="prog-fill" style="width:{pct}%;"></div>
    </div>
    <div style="text-align:right;font-size:11px;color:#bbb;margin-top:4px;">{pct}%</div>
    """, unsafe_allow_html=True)

    html = ""
    for i, (titre, sous) in enumerate(STEPS):
        if i < current:
            icon_cls, icon = "step-done",   "✓"
        elif i == current:
            icon_cls, icon = "step-active", "…"
        else:
            icon_cls, icon = "step-wait",   str(i+1)
        html += f"""
        <div class="step-line">
            <div class="step-icon {icon_cls}">{icon}</div>
            <div>
                <div class="step-text">{titre}</div>
                <div class="step-sub">{sous}</div>
            </div>
        </div>"""
    steps_box.markdown(html, unsafe_allow_html=True)

# Animation étape par étape
for i in range(len(STEPS)):
    render(i, int((i / len(STEPS)) * 90))
    time.sleep(0.8)

# Calcul réel
render(len(STEPS), 95)

@st.cache_resource
def load_rec():
    return Recommender(
        data_dir=os.path.join(os.path.dirname(__file__), "..")
    ).fit()

rec = load_rec()

candidats = rec.recommander(
    cuisine_pref = profil["cuisine"],
    allergies    = profil["allergies"],
    piment_max   = profil["piment"],
    saison       = profil["saison"],
    n            = 10,
)

st.session_state["mm_candidats"] = candidats.to_dict("records") if not candidats.empty else []

render(len(STEPS), 100)
time.sleep(0.4)

st.switch_page("pages/2_notation.py")
