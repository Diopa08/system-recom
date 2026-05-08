import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from styles import inject

st.set_page_config(page_title="MealMatch", layout="centered", initial_sidebar_state="collapsed")

st.markdown(inject("""
.block-container { max-width: 520px !important; padding: 56px 24px 80px !important; }
.app-title { font-family:'DM Serif Display',serif; font-size:30px; font-weight:400; color:#1a1a1a; margin-bottom:6px; }
.app-sub   { font-size:14px; color:#999; margin-bottom:48px; line-height:1.7; }
.stRadio div[role="radiogroup"] label {
    font-size:13px !important; border:0.5px solid #e8e8e0; border-radius:20px;
    padding:5px 14px !important; cursor:pointer; color:#555 !important; background:#fff;
}
.stRadio div[role="radiogroup"] label:has(input:checked) {
    background:#1a1a1a !important; color:#fff !important; border-color:#1a1a1a !important;
}
"""), unsafe_allow_html=True)

st.markdown('<div class="app-title">MealMatch</div>', unsafe_allow_html=True)
st.markdown('<div class="app-sub">Dites-nous qui vous êtes et ce que vous aimez.<br>Nous trouvons les plats et les restaurants faits pour vous.</div>', unsafe_allow_html=True)

with st.form("form_mealmatch"):

    st.markdown('<div class="sep">Votre profil</div>', unsafe_allow_html=True)
    prenom = st.text_input("Prénom", placeholder="ex. Kofi")
    ville  = st.text_input("Ville", placeholder="ex. Cotonou, Dakar, Paris…")

    st.markdown('<div class="sep">Vos goûts</div>', unsafe_allow_html=True)
    cuisine = st.selectbox(
        "Cuisine préférée",
        ["africaine","méditerranéenne","française","asiatique","américaine","italienne","internationale"],
        format_func=lambda x: {
            "africaine"      : "Africaine (béninoise, sénégalaise…)",
            "méditerranéenne": "Méditerranéenne / Moyen-Orient",
            "française"      : "Française",
            "asiatique"      : "Asiatique (japonaise, thaï, indienne…)",
            "américaine"     : "Américaine / Mexicaine",
            "italienne"      : "Italienne",
            "internationale" : "Internationale / Fusion",
        }[x]
    )
    piment = st.radio(
        "Tolérance au piment",
        [0, 1, 2, 3],
        format_func=lambda x: {0:"Pas du tout", 1:"Léger", 2:"Moyen", 3:"Fort"}[x],
        horizontal=True
    )
    saison = st.radio(
        "Saison actuelle",
        ["printemps","été","automne","hiver"],
        format_func=lambda x: x.capitalize(),
        horizontal=True
    )

    st.markdown('<div class="sep">Restrictions alimentaires</div>', unsafe_allow_html=True)
    allergies = st.multiselect(
        "Allergies ou intolérances (optionnel)",
        ["gluten","lait","oeufs","poisson","crustacés","noix","arachides","soja","sésame"],
        format_func=lambda x: x.capitalize(),
        placeholder="Sélectionnez si nécessaire"
    )

    submit = st.form_submit_button("Continuer")

if submit:
    if not prenom.strip():
        st.error("Veuillez entrer votre prénom.")
    elif not ville.strip():
        st.error("Veuillez entrer votre ville.")
    else:
        st.session_state["mm_profil"] = {
            "prenom"   : prenom.strip(),
            "ville"    : ville.strip(),
            "cuisine"  : cuisine,
            "piment"   : piment,
            "saison"   : saison,
            "allergies": allergies,
        }
        st.session_state["mm_notes"]    = {}
        st.session_state["mm_candidats"]= None
        st.switch_page("pages/1_chargement.py")
