import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from styles import inject

st.set_page_config(page_title="Notez les plats", layout="centered", initial_sidebar_state="collapsed")

st.markdown(inject("""
.block-container { max-width: 600px !important; padding: 48px 24px 80px !important; }

.page-title { font-family:'DM Serif Display',serif; font-size:26px; font-weight:400; color:#1a1a1a; margin-bottom:6px; }
.page-sub   { font-size:13px; color:#555; margin-bottom:36px; line-height:1.7; }

.plat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 0.5px solid #f0f0ee;
}
.plat-info { flex: 1; }
.plat-nom  { font-size:15px; font-weight:500; color:#1a1a1a; margin-bottom:3px; }
.plat-meta { font-size:11px; color:#666; }

.stars-row { display:flex; gap:4px; }
.star {
    font-size: 22px;
    cursor: pointer;
    color: #e0e0da;
    transition: color 0.1s, transform 0.1s;
    line-height: 1;
    user-select: none;
}
.star.filled { color: #F5A623; }
.star:hover  { transform: scale(1.15); }

.tag-piment-1 { color:#BA7517; font-size:11px; }
.tag-piment-2 { color:#D4620A; font-size:11px; }
.tag-piment-3 { color:#C0392B; font-size:11px; }

.compteur {
    text-align: center;
    font-size:12px;
    color:#666;
    margin-bottom: 24px;
}
.compteur b { color:#1a1a1a; }

.progress-dots {
    display: flex;
    justify-content: center;
    gap: 6px;
    margin-bottom: 32px;
}
.dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #e8e8e0;
}
.dot.filled { background: #1a1a1a; }

.skip-note {
    font-size: 11px;
    color: #777;
    text-align: center;
    margin-top: 8px;
}
"""), unsafe_allow_html=True)

# Vérification session
if "mm_profil" not in st.session_state or "mm_candidats" not in st.session_state:
    st.switch_page("accueil.py")

profil    = st.session_state["mm_profil"]
candidats = st.session_state.get("mm_candidats", [])

if not candidats:
    st.warning("Aucun plat trouvé. Revenez au formulaire.")
    if st.button("Retour"):
        st.switch_page("accueil.py")
    st.stop()

# Initialiser les notes
if "mm_notes" not in st.session_state:
    st.session_state["mm_notes"] = {}

notes = st.session_state["mm_notes"]
n_notes = sum(1 for v in notes.values() if v > 0)

# ── En-tête ──────────────────────────────────────────────
st.markdown(f'<div class="page-title">Notez ces plats, {profil["prenom"]}</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Dites-nous ce que vous aimez — notez les plats que vous connaissez, ignorez les autres. Cela nous permet d\'affiner vos recommandations.</div>', unsafe_allow_html=True)

# Barre de progression
dots_html = "".join([
    f'<div class="dot {"filled" if i < n_notes else ""}"></div>'
    for i in range(len(candidats))
])
st.markdown(f'<div class="progress-dots">{dots_html}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="compteur"><b>{n_notes}</b> / {len(candidats)} plats notés</div>', unsafe_allow_html=True)

# ── Liste des plats avec étoiles ──────────────────────────
PIMENT_LABELS = {0:"", 1:"piment léger", 2:"piment", 3:"piment fort"}
PIMENT_CLASS  = {0:"", 1:"tag-piment-1", 2:"tag-piment-2", 3:"tag-piment-3"}

for plat in candidats:
    mid      = int(plat["meal_id"])
    nom      = plat["nom"]
    cuisine  = str(plat["cuisine"]).capitalize()
    piment_v = int(plat["piment"])
    note_act = notes.get(mid, 0)

    piment_html = f'<span class="{PIMENT_CLASS[piment_v]}">{PIMENT_LABELS[piment_v]}</span>' if piment_v > 0 else ""
    meta_parts = [cuisine]
    if piment_v > 0:
        meta_parts.append(PIMENT_LABELS[piment_v])
    meta = " · ".join(meta_parts)

    # Afficher nom + meta
    st.markdown(f"""
    <div style="padding:14px 0 8px; border-bottom:0.5px solid #f8f8f6;">
        <div class="plat-nom">{nom}</div>
        <div class="plat-meta">{meta}</div>
    </div>
    """, unsafe_allow_html=True)

    # Étoiles avec radio button stylisé
    cols = st.columns([1, 1, 1, 1, 1, 2])
    LABELS = {1:"Pas aimé", 2:"Bof", 3:"Correct", 4:"Bon", 5:"Excellent"}

    for i, col in enumerate(cols[:5]):
        star_val = i + 1
        is_filled = note_act >= star_val
        color = "#F5A623" if is_filled else "#e0e0da"
        if col.button("★", key=f"star_{mid}_{star_val}",
                      help=LABELS[star_val],
                      use_container_width=True):
            # Si on clique sur l'étoile déjà sélectionnée → déselectionner
            if note_act == star_val:
                st.session_state["mm_notes"][mid] = 0
            else:
                st.session_state["mm_notes"][mid] = star_val
            st.rerun()

    with cols[5]:
        if note_act > 0:
            label_note = {1:"Pas aimé", 2:"Bof", 3:"Correct", 4:"Bon", 5:"Excellent"}
            st.markdown(f'<div style="font-size:12px;color:#F5A623;padding-top:8px;font-weight:500;">{label_note[note_act]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:11px;color:#ddd;padding-top:10px;">non noté</div>', unsafe_allow_html=True)

# Rendu visuel des étoiles remplies via JS
stars_js = ""
for plat in candidats:
    mid      = int(plat["meal_id"])
    note_act = notes.get(mid, 0)
    for i in range(1, 6):
        color = "#F5A623" if note_act >= i else "#e0e0da"
        # On injecte la couleur via un hack CSS ciblé
        stars_js += f"""
        [data-testid="stButton"][key="star_{mid}_{i}"] button {{
            color:#222 !important;
            background: none !important;
            border: none !important;
            font-size: 22px !important;
            padding: 4px !important;
        }}
        """

st.markdown(f"""
<style>
/* Style des boutons étoiles */
div[data-testid="stButton"] button {{
    background: none !important;
    border: none !important;
    font-size: 20px !important;
    padding: 2px 4px !important;
    color: #e0e0da !important;
    box-shadow: none !important;
    min-height: 0 !important;
    height: auto !important;
}}
div[data-testid="stButton"] button:hover {{
    color: #F5A623 !important;
    transform: scale(1.2);
    background: none !important;
    border: none !important;
}}
</style>
""", unsafe_allow_html=True)

# Colorier les étoiles remplies via la valeur actuelle
for plat in candidats:
    mid      = int(plat["meal_id"])
    note_act = notes.get(mid, 0)
    if note_act > 0:
        filled_keys = " , ".join([f'button[aria-label="star_{mid}_{i}"]' for i in range(1, note_act+1)])
        st.markdown(f"""
        <style>
        /* Highlight étoiles notées pour meal {mid} — note {note_act} */
        </style>
        <script>
        (function() {{
            const btns = document.querySelectorAll('button');
            btns.forEach(b => {{
                const key = b.closest('[data-testid="stButton"]')?.getAttribute('data-testid');
            }});
        }})();
        </script>
        """, unsafe_allow_html=True)

st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

# ── Boutons de navigation ─────────────────────────────────
c1, c2 = st.columns([1, 2])
with c1:
    st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
    if st.button("Retour", key="btn_retour"):
        st.switch_page("accueil.py")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    n_notes_now = sum(1 for v in st.session_state["mm_notes"].values() if v > 0)
    label_btn = f"Voir mes recommandations ({n_notes_now} notes)" if n_notes_now > 0 else "Continuer sans noter"
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
    if st.button(label_btn, key="btn_suivant"):
        st.switch_page("pages/3_resultats.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f'<div class="skip-note">Vous pouvez continuer sans noter — nous utiliserons vos préférences de profil.</div>', unsafe_allow_html=True)
