"""Look & feel: custom CSS + hero banner."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Poppins', 'Segoe UI', sans-serif; }
.stApp { background: radial-gradient(1200px 600px at 10% -10%, #2a1f5c55 0%, transparent 60%),
                     radial-gradient(900px 500px at 100% 0%, #0e7c8a40 0%, transparent 55%), #0B1020; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #151B33 0%, #0f1428 100%); border-right: 1px solid #ffffff14; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1200px; }

.hero { background: linear-gradient(120deg, #6d3df5 0%, #8b5cf6 40%, #0ea5b7 100%); border-radius: 22px;
        padding: 28px 32px; margin-bottom: 18px; box-shadow: 0 14px 40px #6d3df540; color: #fff; }
.hero h1 { margin: 0; font-size: 2.2rem; font-weight: 700; letter-spacing: -0.5px; }
.hero p { margin: 6px 0 14px 0; opacity: .92; font-size: 1.02rem; }
.chip { display: inline-block; background: #ffffff26; border: 1px solid #ffffff40; padding: 5px 13px; border-radius: 999px;
        margin: 3px 6px 0 0; font-size: .82rem; font-weight: 500; backdrop-filter: blur(4px); }

button[data-baseweb="tab"] { border-radius: 999px !important; padding: 8px 16px !important; margin-right: 6px; background: #ffffff0d;
        border: 1px solid #ffffff14 !important; }
button[data-baseweb="tab"][aria-selected="true"] { background: linear-gradient(120deg, #6d3df5, #8b5cf6) !important; color: #fff !important; }
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }

.stButton > button, .stDownloadButton > button { border-radius: 12px; border: 1px solid #ffffff22; font-weight: 600; transition: all .15s ease; }
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-2px); border-color: #8b5cf6; box-shadow: 0 8px 20px #8b5cf633; }
button[kind="primary"], button[data-testid="stBaseButton-primary"] { background: linear-gradient(120deg, #6d3df5, #0ea5b7) !important; border: 0 !important; color: #fff !important; }

[data-testid="stMetric"] { background: #ffffff0d; border: 1px solid #ffffff1a; border-radius: 16px; padding: 14px 18px; }
[data-testid="stExpander"] { border: 1px solid #ffffff1a; border-radius: 14px; background: #ffffff08; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border-radius: 12px; overflow: hidden; }
h2, h3, h4 { font-weight: 600; letter-spacing: -0.2px; }
.stTextInput input, .stTextArea textarea, .stDateInput input { border-radius: 10px !important; }

.lockcard { background: #ffffff0a; border: 1px solid #ffffff1a; border-radius: 20px; padding: 6px 22px 22px 22px; }
.stepbox { background: #8b5cf61a; border-left: 4px solid #8b5cf6; padding: 10px 14px; border-radius: 8px; margin: 6px 0 12px 0; font-size: .92rem; }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title, subtitle, chips):
    chips_html = "".join(f"<span class='chip'>{c}</span>" for c in chips)
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p>{chips_html}</div>", unsafe_allow_html=True)
