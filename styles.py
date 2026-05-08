FONTS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=DM+Serif+Display&display=swap');
"""

BASE = """
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #1a1a1a;
    background: #fff;
}
#MainMenu, footer, header, [data-testid="stSidebarNav"] { visibility: hidden; }

.stButton > button {
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    letter-spacing: 0.03em;
    border-radius: 6px;
    padding: 9px 20px;
    cursor: pointer;
    transition: all 0.15s;
}
.btn-primary > button {
    background: #1a1a1a !important;
    color: #fff !important;
    border: none !important;
    width: 100%;
    padding: 13px !important;
}
.btn-primary > button:hover { background: #333 !important; }
.btn-secondary > button {
    background: none !important;
    border: 0.5px solid #e0e0da !important;
    color: #888 !important;
}
.btn-secondary > button:hover { border-color: #1a1a1a !important; color: #1a1a1a !important; }

.sep {
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #ccc;
    border-bottom: 0.5px solid #f0f0ee;
    padding-bottom: 8px;
    margin: 28px 0 18px;
}
.stAlert { border-radius: 6px !important; font-size: 13px !important; }

.stTextInput > label, .stSelectbox > label,
.stMultiSelect > label, .stSlider > label, .stRadio > label {
    font-size: 12px !important; color: #888 !important;
    font-weight: 400 !important; letter-spacing: 0.02em !important;
}
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div:first-child {
    border-color: #e8e8e0 !important;
    border-radius: 6px !important;
    background: #fff !important;
}
span[data-baseweb="tag"] { background: #f0f0ee !important; border-radius: 4px !important; }
.stRadio div[role="radiogroup"] { flex-direction: row !important; gap: 8px !important; flex-wrap: wrap; }
"""

def inject(extra=""):
    return f"<style>{FONTS}{BASE}{extra}</style>"
