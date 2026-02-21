import streamlit as st
import os

DONATION_LINK = "https://www.buymeacoffee.com/80percentbill"

_CSS = """
<style>
    /* === DESIGN TOKENS === */
    :root {
        --blue-primary: #1E3A5F;
        --blue-hover: #2c5282;
        --red-accent: #C41E3A;
        --red-hover: #a01830;
        --white: #FFFFFF;
        --gray-light: #F7F8FA;
        --gray-text: #4A5568;
        --gray-border: #E2E8F0;
    }

    /* === HIDE SIDEBAR NAV (all known selectors) === */
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"],
    [data-testid="stSidebarNavSeparator"],
    [data-testid="stSidebarNavLink"],
    [data-testid="stSidebar"] nav,
    [data-testid="stSidebar"] ul,
    section[data-testid="stSidebar"] > div:first-child > div > ul { display: none !important; }

    /* === GLOBAL: White Background === */
    [data-testid="stAppViewContainer"] {
        background-color: var(--white) !important;
    }
    [data-testid="stHeader"] {
        background-color: var(--white) !important;
        border-bottom: 1px solid var(--gray-border);
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 900px;
    }

    /* === TYPOGRAPHY: Blue for headings === */
    h1, h2, h3, h4 {
        color: var(--blue-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    h1 { font-size: 2.25rem !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.5rem !important; }
    h3 { font-size: 1.25rem !important; }
    p, li, label, .stMarkdown {
        color: var(--gray-text) !important;
        font-weight: 500 !important;
    }
    strong, b {
        font-size: 1.1em !important;
        font-weight: 700 !important;
    }

    /* === INPUT FIELDS === */
    [data-testid="stTextInput"] input,
    [data-testid="stTextInput"] textarea,
    input[type="text"],
    input[type="email"],
    textarea {
        background-color: var(--white) !important;
        border: 1px solid var(--gray-border) !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        font-size: 1rem !important;
    }
    [data-testid="stTextInput"] > div {
        border: none !important;
        box-shadow: none !important;
    }
    input:focus, textarea:focus {
        border-color: var(--red-accent) !important;
        box-shadow: 0 0 0 2px rgba(196, 30, 58, 0.12) !important;
        outline: none !important;
    }
    ::placeholder { color: #94A3B8 !important; }

    /* === PRIMARY BUTTONS: Blue with Red hover === */
    .stButton > button {
        background-color: var(--blue-primary) !important;
        color: var(--white) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        min-height: 44px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: var(--red-accent) !important;
        transform: translateY(-1px);
    }
    .stButton > button * { color: var(--white) !important; }

    /* === LINK BUTTONS === */
    [data-testid="stLinkButton"] {
        background-color: var(--red-accent) !important;
        color: var(--white) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stLinkButton"]:hover { background-color: var(--red-hover) !important; }
    [data-testid="stLinkButton"] p,
    [data-testid="stLinkButton"] a,
    [data-testid="stLinkButton"] span,
    [data-testid="stLinkButton"] * { color: var(--white) !important; }

    /* === SIDEBAR: Blue gradient === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--blue-primary) 0%, #152a47 100%) !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {
        color: var(--white) !important;
    }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.3) !important; }
    [data-testid="stSidebar"] [data-testid="stLinkButton"] {
        background-color: var(--red-accent) !important;
        color: var(--white) !important;
        border: 2px solid rgba(255,255,255,0.3) !important;
    }
    [data-testid="stSidebar"] [data-testid="stLinkButton"]:hover,
    [data-testid="stSidebar"] [data-testid="stLinkButton"]:focus {
        background-color: var(--red-hover) !important;
    }
    [data-testid="stSidebar"] [data-testid="stLinkButton"] p,
    [data-testid="stSidebar"] [data-testid="stLinkButton"] a,
    [data-testid="stSidebar"] [data-testid="stLinkButton"] span,
    [data-testid="stSidebar"] [data-testid="stLinkButton"] * { color: var(--white) !important; }
    [data-testid="stSidebar"] [data-testid="stExpander"],
    [data-testid="stSidebar"] details {
        background-color: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.3) !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] p,
    [data-testid="stSidebar"] [data-testid="stExpander"] label,
    [data-testid="stSidebar"] [data-testid="stExpander"] .stMarkdown,
    [data-testid="stSidebar"] [data-testid="stExpander"] button,
    [data-testid="stSidebar"] [data-testid="stExpander"] button *,
    [data-testid="stSidebar"] details p,
    [data-testid="stSidebar"] details label,
    [data-testid="stSidebar"] details .stMarkdown,
    [data-testid="stSidebar"] details button,
    [data-testid="stSidebar"] details button *,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary,
    [data-testid="stSidebar"] details summary { color: var(--white) !important; }

    /* === ARTICLE BOXES === */
    .article-box {
        background: var(--white);
        border: 2px solid var(--gray-border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid var(--blue-primary);
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .article-box:hover {
        border-left-color: var(--red-accent);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.08);
    }
    .article-title {
        color: var(--blue-primary) !important;
        font-size: 1.125rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }
    .article-desc {
        color: var(--gray-text) !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
    }
    .note-text {
        color: var(--gray-text) !important;
        background-color: var(--gray-light);
        padding: 0.75rem 1rem;
        font-size: 0.875rem !important;
        font-style: italic;
        border-radius: 8px;
        margin-top: 0.75rem;
    }
    a.bill-link {
        display: inline-block;
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        background-color: var(--red-accent);
        color: var(--white) !important;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.9rem;
        transition: background-color 0.2s;
    }
    a.bill-link:hover {
        background-color: var(--red-hover);
        color: var(--white) !important;
    }
    a.donate-success-btn {
        display: inline-block;
        background-color: var(--red-accent) !important;
        color: var(--white) !important;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 1rem;
        transition: background-color 0.2s;
    }
    a.donate-success-btn:hover {
        background-color: var(--red-hover) !important;
        color: var(--white) !important;
    }

    /* === FORM === */
    [data-testid="stForm"] {
        background: var(--white);
        border: 2px solid var(--gray-border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* === ALERTS === */
    [data-testid="stAlert"] {
        border-radius: 10px;
        border-left-width: 4px !important;
    }

    /* === MOBILE === */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 1rem 2rem;
            max-width: 100%;
        }
        h1 { font-size: 1.75rem !important; }
        h2 { font-size: 1.25rem !important; }
        .article-box { padding: 1rem; }
        .article-title { font-size: 1rem !important; }
        .stButton > button {
            width: 100% !important;
            min-height: 48px !important;
        }
        [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }

    /* === TABLET === */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container { max-width: 700px; }
    }
</style>
"""


def inject_theme():
    """Inject shared CSS. Call once per app run (from app.py)."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _find_logo():
    for name in ["Gemini_Generated_Image_1dkkh41dkkh41dkk.jpg", "logo.jpg", "logo.png"]:
        if os.path.exists(name):
            return name
    return None


LOGO_IMG = _find_logo()
