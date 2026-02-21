
import streamlit as st
import requests
import pandas as pd
from streamlit_searchbox import st_searchbox
import random
import os
import backup_service
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
# These keys are now securely loaded from your secrets.toml file
GEOCODIO_API_KEY = st.secrets["GEOCODIO_API_KEY"]
EMAIL_ADDRESS = "the.80.percent.bill@gmail.com"
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]

DONATION_LINK = "https://www.buymeacoffee.com/80percentbill" 

# --- SMART ASSET LOADER ---
def find_image(options):
    for img in options:
        if os.path.exists(img):
            return img
    return None

LOGO_IMG = find_image(["Gemini_Generated_Image_1dkkh41dkkh41dkk.jpg", "logo.jpg", "logo.png"])

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=300)
def get_osm_addresses(search_term):
    """Fetch up to 6 address suggestions from OpenStreetMap Nominatim for US addresses."""
    if not search_term or len(search_term.strip()) < 3:
        return []
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "The80PercentPledge/1.0"}
    params = {"q": search_term, "format": "json", "limit": 6, "countrycodes": "us", "addressdetails": 1}
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return []
    return []

def get_district(address):
    """Use Geocodio API to convert address to congressional district and representative."""
    if not address:
        return None, None
    url = "https://api.geocod.io/v1.7/geocode"
    params = {"q": address, "fields": "cd", "api_key": GEOCODIO_API_KEY}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                data = results[0]
                fields = data.get('fields', {})
                if 'congressional_districts' in fields:
                    dist_data = fields['congressional_districts'][0]
                    state = data.get('address_components', {}).get('state', '')
                    dist_num = dist_data.get('district_number')
                    if state is not None and dist_num is not None:
                        legislators = dist_data.get('current_legislators', [])
                        rep_name = "Vacant"
                        for leg in legislators:
                            if leg.get('type') == 'representative':
                                rep = leg.get('bio', {})
                                rep_name = f"{rep.get('first_name', '')} {rep.get('last_name', '')}".strip()
                                break
                        return f"{state}-{dist_num}", rep_name
    except Exception:
        pass
    return None, None

def is_duplicate(email):
    # CHECKS GOOGLE SHEETS FOR DUPLICATES
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Read only the Email column (index 2) to be fast
        df = conn.read(worksheet="Sheet1", usecols=[2], ttl=0)
        if df is not None and not df.empty:
            existing_emails = df.iloc[:, 0].astype(str).str.strip().str.lower().values
            return email.strip().lower() in existing_emails
    except Exception:
        return False
    return False

def send_email_code(to_email):
    code = str(random.randint(1000, 9999))
    try:
        msg = MIMEText(f"Your 80% Pledge verification code is: {code}")
        msg['Subject'] = "Verification Code - The 80% Pledge"
        msg['From'] = f"The 80% Pledge <{EMAIL_ADDRESS}>"
        msg['To'] = to_email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        return code
    except Exception as e:
        # SILENT FAILURE: Return None so the app knows to skip verification
        print(f"Email failed (likely limit hit): {e}") 
        return None


def save_pledge(name, email, district, rep_name):
    # 1. Trigger the Backup Program FIRST (The Vault)
    # This runs blindly so it saves data even if the main sheet fails.
    backup_service.save_to_vault(name, email, district, rep_name)

    # 2. Save to the Main Public Sheet
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Force a fresh download
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        
        # --- CRITICAL SAFETY ---
        # Abort only if sheet is empty (read error) - allow saves with any non-empty data
        if existing_data is None or existing_data.empty:
            st.error("⚠️ CRITICAL SAFETY LOCK: Database read returned 0 rows. Save aborted to protect data.")
            return False
        # -------------------------------

        # Create the new row
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": name,
            "Email": email,
            "District": district,
            "Rep": rep_name
        }])
        
        # Combine
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        
        # SAFETY CHECK 2: THE "ANTI-WIPE" LOCK (Redundant but kept for double safety)
        if len(updated_df) < len(existing_data):
            st.error(f"⚠️ SAFETY LOCK TRIGGERED: Attempted to delete data. (Old: {len(existing_data)}, New: {len(updated_df)})")
            return False
            
        # Upload
        conn.update(worksheet="Sheet1", data=updated_df)
        return True
        
    except Exception as e:
        err_msg = str(e).lower()
        if "permission" in err_msg or "403" in err_msg or "credentials" in err_msg or "unauthorized" in err_msg:
            st.error(
                "⚠️ Google Sheets write failed (likely read-only connection). "
                "To save pledges, use Service Account auth—see SECRETS_SETUP.md"
            )
        else:
            st.error(f"⚠️ GOOGLE SHEETS ERROR: {e}")
        return False
        
# --- THE APP UI ---

st.set_page_config(
    page_title="The 80% Bill",
    page_icon="🇺🇸",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# --- CUSTOM THEME: White background, Blue primary, Red accents ---
st.markdown("""
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
    /* Single 1px border - avoid double-border effect from nested elements */
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
    /* Suppress outer border/outline on Streamlit input containers */
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
        min-height: 44px !important;  /* Touch-friendly on mobile */
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: var(--red-accent) !important;
        transform: translateY(-1px);
    }
    .stButton > button * { color: var(--white) !important; }

    /* === LINK BUTTONS (main content - donation, etc.) === */
    [data-testid="stLinkButton"] {
        background-color: var(--red-accent) !important;
        color: var(--white) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stLinkButton"]:hover {
        background-color: var(--red-hover) !important;
    }
    [data-testid="stLinkButton"] p,
    [data-testid="stLinkButton"] a,
    [data-testid="stLinkButton"] span,
    [data-testid="stLinkButton"] * {
        color: var(--white) !important;
    }

    /* === SIDEBAR: Blue with red accent button === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--blue-primary) 0%, #152a47 100%) !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {
        color: var(--white) !important;
    }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.3) !important; }
    /* Sidebar donation button - ensure text is always visible */
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
    [data-testid="stSidebar"] [data-testid="stLinkButton"] * {
        color: var(--white) !important;
    }
    /* Admin expander: ensure text has contrast on blue sidebar */
    [data-testid="stSidebar"] [data-testid="stExpander"],
    [data-testid="stSidebar"] details,
    [data-testid="stSidebar"] [data-baseweb="expansion-panel"] {
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
    [data-testid="stSidebar"] details summary,
    [data-testid="stSidebar"] [data-baseweb="expansion-panel"] * {
        color: var(--white) !important;
    }

    /* === TABS === */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 0;
        background-color: var(--gray-light);
        border-radius: 10px;
        padding: 4px;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background-color: var(--blue-primary) !important;
        color: var(--white) !important;
    }
    /* Force white text on selected tab (child elements often override parent color) */
    [data-testid="stTabs"] [aria-selected="true"] * {
        color: var(--white) !important;
    }
    [data-testid="stTabs"] [aria-selected="false"] {
        color: var(--gray-text) !important;
    }

    /* === FORM CARD: Clean container === */
    .pledge-card {
        background: var(--white);
        border: 2px solid var(--gray-border);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
    }

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
    /* Success screen donate button - always visible (red bg, white text) */
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

    /* === CAPTION / HINTS === */
    [data-testid="stCaptionContainer"] {
        color: var(--gray-text) !important;
        font-size: 0.9rem !important;
    }

    /* === FORM CARD STYLING === */
    [data-testid="stForm"] {
        background: var(--white);
        border: 2px solid var(--gray-border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* === ALERTS: Softer styling === */
    [data-testid="stAlert"] {
        border-radius: 10px;
        border-left-width: 4px !important;
    }

    /* === MOBILE RESPONSIVE === */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 1rem 2rem;
            max-width: 100%;
        }
        h1 { font-size: 1.75rem !important; }
        h2 { font-size: 1.25rem !important; }
        .pledge-card { padding: 1.25rem; }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            padding: 0.6rem 1rem;
            font-size: 0.9rem;
        }
        .article-box {
            padding: 1rem;
        }
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
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    if LOGO_IMG: st.image(LOGO_IMG, width="stretch")
    else: st.header("🇺🇸 The 80% Bill")
    st.divider()
    st.header("Support the Project")
    st.link_button("☕ Buy me a Coffee ($5)", DONATION_LINK, type="primary", width="stretch")
    st.divider()
    
    # --- ADMIN PANEL (Google Sheets Version) ---
    with st.expander("Admin Access"):
        if st.button("Check Connection"):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Sheet1", ttl=0)
                st.success(f"Connected! Total Signatures: {len(df)}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")

# --- MAIN PAGE ---

st.title("The 80% Bill")
st.markdown(
    '<p style="color: #4A5568; font-size: 1.1rem; margin-top: -0.5rem;">20 bills that 80%+ of Americans support. Sign the pledge.</p>',
    unsafe_allow_html=True,
)
st.markdown("---")

tab1, tab2 = st.tabs(["✍️ Add Your Name", "📖 Read the Bill"])

with tab1:
    if 'step' not in st.session_state: st.session_state.step = 1

    st.info("**Pledge:** By completing this form, I state that I will not vote for anyone who does not actively support this bill.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # --- STEP 1: DISTRICT ENTRY (Manual or Address Lookup) ---
        if st.session_state.step == 1:
            st.subheader("Step 1: Enter your District")
            
            # Address lookup - updates live as you type (debounced), click address to populate fields
            st.markdown("**Enter your address to look up this info:**")

            def address_search(searchterm: str):
                """Returns up to 6 address suggestions - called as user types (debounced)."""
                return [
                    r.get("display_name")
                    for r in get_osm_addresses(searchterm)
                    if r.get("display_name")
                ][:6]

            def on_address_select(selected_address):
                """When user clicks an address: populate district/rep fields only (stay on same page)."""
                if selected_address:
                    district, rep = get_district(selected_address)
                    if district and rep:
                        st.session_state.district_info = (district, rep)
                        st.session_state.district_input = district
                        st.session_state.rep_input = rep
                        st.session_state.address_just_populated = True
                        if "address_lookup_error" in st.session_state:
                            del st.session_state["address_lookup_error"]
                        st.rerun()
                    else:
                        st.session_state.address_lookup_error = "Could not find congressional district."

            st_searchbox(
                address_search,
                key="address_searchbox",
                placeholder="Type to search (addresses appear below as you type)",
                debounce=600,
                clear_on_submit=False,
                submit_function=on_address_select,
            )
            if st.session_state.get("address_lookup_error"):
                st.error(st.session_state["address_lookup_error"])
                del st.session_state["address_lookup_error"]

            if st.session_state.get("address_just_populated"):
                st.success("✓ **Filled in!** Verify your district and representative below, then click **Continue to Sign**.")
                del st.session_state["address_just_populated"]

            st.markdown("---")
            st.markdown("**Or enter manually:**")
            # Initialize from district_info only when keys don't exist (e.g. first load or return from step 2)
            if "district_input" not in st.session_state:
                st.session_state.district_input = st.session_state.district_info[0] if "district_info" in st.session_state else ""
            if "rep_input" not in st.session_state:
                st.session_state.rep_input = st.session_state.district_info[1] if "district_info" in st.session_state else ""
            manual_dist = st.text_input(
                "District Code:",
                placeholder="e.g. NY-14",
                key="district_input",
            )
            manual_rep = st.text_input(
                "Representative Name:",
                placeholder="e.g. Alexandria Ocasio-Cortez",
                key="rep_input",
            )

            if st.button("Continue to Sign", key="continue_manual"):
                if manual_dist and manual_rep:
                    st.session_state.district_info = (manual_dist, manual_rep)
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.error("Please fill in both District Code and Representative Name.")

        # --- STEP 2: ENTER INFO & SAVE (NO EMAIL CODE) ---
        elif st.session_state.step == 2:
            dist, rep = st.session_state.district_info
            st.success(f"You are in **{dist}** represented by **{rep}**.")
            
            if st.button("Wrong District? Change it."):
                st.session_state.step = 1
                st.rerun()

            with st.form("contact_form"):
                st.subheader("Step 2: Sign the Pledge")
                name = st.text_input("Full Name")
                email_input = st.text_input("Email Address")
                
                if st.form_submit_button("I will not vote for anyone who does not support this bill, unaltered"):
                    if name and email_input and "@" in email_input:
                        clean_email = email_input.strip().lower()
                        
                        # CHECK FOR DUPLICATES
                        if is_duplicate(clean_email): 
                            st.error(f"❌ '{clean_email}' has already signed.")
                        else:
                            # SAVE IMMEDIATELY (No Verification)
                            save_pledge(name, clean_email, dist, rep)
                            
                            # Move to Success Screen
                            st.session_state.step = 3
                            st.rerun()
                    else: st.error("Invalid email.")

        # --- STEP 3: SUCCESS SCREEN ---
        elif st.session_state.step == 3:
            st.balloons()
            st.success("**Thank you!** Your name has been added to the pledge.")
            st.markdown("")
            st.markdown(
                f'<a href="{DONATION_LINK}" target="_blank" rel="noopener noreferrer" class="donate-success-btn">❤️ Donate $5 to help spread the word</a>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            if st.button("Sign Another Person"):
                st.session_state.clear()
                st.rerun()
                    
with tab2:
    st.markdown(
        "### Every article below is supported by at least 80% of American voters.\n\n"
        "Browse the bills, read the details, and click through to Congress.gov for the full legislation."
    )
    
# FORMAT: (Title, Description, Link, Optional_Note)
    articles = [

        (
            "I. Ban Congressional Stock Trading", 
            "Prohibits Members, their spouses, and dependent children from owning or trading individual stocks. Requires full divestment or a qualified blind trust.", 
            "https://www.congress.gov/bill/118th-congress/senate-bill/1171", None
        ),
        ("II. End Forever Wars", "Repeal outdated authorizations (AUMFs) to return war powers to Congress.", "https://www.congress.gov/bill/118th-congress/senate-bill/316", None),
        ("III. Lifetime Lobbying Ban", "Former Members of Congress are banned for life from becoming registered lobbyists.", "https://www.congress.gov/bill/118th-congress/house-bill/1601", None),
        ("IV. Tax the Ultra-Wealthy", "Close tax loopholes and establish a minimum tax for billionaires.", "https://www.congress.gov/bill/118th-congress/house-bill/6498", None),
        (
            "V. Ban Corporate PACs", 
            "Prohibit for-profit corporations from forming Political Action Committees.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/5941", 
            "Note: This legislation includes a 'severability clause.' If the Supreme Court strikes down this specific ban, the rest of the 80% Bill remains law."
        ),
        ("VI. Audit the Pentagon", "The Pentagon has never passed an audit. Require a full, independent audit to root out waste and fraud.", "https://www.congress.gov/bill/118th-congress/house-bill/2961", None),
        (
            "VII. Medicare Drug Negotiation", 
            "1. H.R. 4895: Expands negotiation to 50 drugs/year and applies lower prices to private insurance.\\n2. H.R. 853: Closes the 'Orphan Drug' loophole.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/4895", 
            "Note: This entry combines two bills to protect all Americans (not just seniors) and stop Big Pharma from gaming the 'rare disease' system."
        ),
        (
            "VIII. Fair Elections & End Gerrymandering", 
            "Pass the 'Freedom to Vote Act' to ban partisan gerrymandering and the 'John Lewis Act' to restore the Voting Rights Act.", 
            "https://www.congress.gov/bill/117th-congress/house-bill/5746", None
        ),
        (
            "IX. Protect US Farmland", 
            "Ban adversarial foreign governments from buying American farmland. Includes a 'Beneficial Ownership' registry to stop shell companies.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/9456", None
        ),

        (
            "X. Ban Corporate Purchase of Single Family Homes", 
            "Imposes a massive tax penalty on corporations buying *existing* homes, making it unprofitable. Explicitly allows them to *build* new rental homes to increase supply.", 
            "https://www.congress.gov/bill/118th-congress/senate-bill/3402", 
            "Note: This uses an excise tax (not a ban) to bypass the 'Takings Clause' and forces hedge funds to sell existing homes over 10 years."
        ),
        (
            "XI. Fund Social Security", 
            "Lifts the cap on wages AND taxes investment income (Capital Gains) for earners over $400k. Prevents billionaires from dodging the tax by taking 'stock' instead of 'salary'.", 
            "https://www.congress.gov/bill/118th-congress/senate-bill/1174", 
            None
        ),
        (
            "XII. Police Body Cameras", 
            "Mandates cameras for federal officers and cuts funding to states that don't comply. Includes a 'Presumption of Release' clause so police can't hide footage.", 
            "https://www.congress.gov/bill/117th-congress/house-bill/1280", 
            None
        ),
        (
            "XIII. Ban 'Dark Money' (Overturn Citizens United)", 
            "A provision to overturn *Citizens United* and ban corporate dark money. Requires a 2/3rds vote to survive the Supreme Court.", 
            "https://www.congress.gov/bill/118th-congress/house-joint-resolution/54", 
            "Severability Note: This clause overturns Citizens United, but we acknowledge it will be struck down by the Court unless this bill passes with the votes required to amend the Constitution (2/3rds)."
        ),
        (
            "XIV. Paid Family Leave", 
            "Guarantees 12 weeks of paid leave funded by a payroll insurance fund. Explicitly prohibits firing workers (of any company size) for taking this leave.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/3481", 
            None
        ),
        (
           "XV. Release the Epstein Files", 
            "Mandates the full, unredacted release of all documents, including those hidden by previous partial releases.", 
            "https://www.congress.gov/bill/119th-congress/house-resolution/577", 
            "Note: While some files were released in late 2025, many names were redacted. This resolution demands the immediate release of ALL documents without hiding names."
        ),
        (
            "XVI. Veterans Care Choice", 
            "Codifies the right to private care but mandates strict network adequacy standards so doctors actually accept the coverage. Cuts the red tape on 'Pre-Authorization'.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/8371", 
            None
        ),
        (
            "XVII. The DISCLOSE Act", 
            "Requires immediate disclosure of donors ($10k+) and includes 'Trace-Back' rules to follow money through shell companies to the original source.", 
            "https://www.congress.gov/bill/118th-congress/senate-bill/512", 
            None
        ),
        (
            "XVIII. Close Tax Loopholes", 
            "Reclassifies 'Carried Interest' as ordinary income, regardless of holding period. Ensures hedge fund managers pay the same tax rate as nurses and teachers.", 
            "https://www.congress.gov/bill/118th-congress/senate-bill/4123", 
            None
        ),
        (
            "XIX. Right to Repair (Ban 'Parts Pairing')", 
            "Guarantees access to parts/manuals for cars AND electronics. Explicitly bans 'software pairing' that blocks genuine 3rd-party repairs.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/906", 
            "Note: This entry combines the automotive 'REPAIR Act' (H.R. 906) with the 'Fair Repair Act' standards to stop companies from using software to kill independent repair."
        ),
        (
            "XX. Ban Junk Fees", 
            "Requires 'all-in' price disclosure for travel, tickets, and utilities. Prohibits companies from raising the price (dynamic pricing) once it is shown to the consumer.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/2463", 
            None
        )
    ]

    for title, desc, link, note in articles:
        note_html = f"<div class='note-text'>{note}</div>" if note else ""
        html_block = f"""<div class="article-box"><div class="article-title">{title}</div><div class="article-desc">{desc}</div>{note_html}<a href="{link}" target="_blank" class="bill-link">🏛️ Read the Bill</a></div>"""
        st.markdown(html_block, unsafe_allow_html=True)
