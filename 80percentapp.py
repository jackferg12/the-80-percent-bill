
import streamlit as st
import requests
import csv
import os
import pandas as pd
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
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

# We only look for the LOGO now, since the Banner is removed
LOGO_IMG = find_image(["Gemini_Generated_Image_1dkkh41dkkh41dkk.jpg", "logo.jpg", "logo.png"])

# --- HELPER FUNCTIONS ---
def get_osm_addresses(search_term):
    if not search_term: return []
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "The80PercentPledge/1.0"}
    params = {"q": search_term, "format": "json", "limit": 5, "countrycodes": "us", "addressdetails": 1}
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
    except:
        return []
    return []

def get_district(address):
    if not address: return None, None
    url = "https://api.geocod.io/v1.7/geocode"
    params = {"q": address, "fields": "cd", "api_key": GEOCODIO_API_KEY}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                data = results[0]
                if 'congressional_districts' in data['fields']:
                    dist_data = data['fields']['congressional_districts'][0]
                    state = data['address_components']['state']
                    dist_num = dist_data['district_number']
                    legislators = dist_data.get('current_legislators', [])
                    rep_name = "Vacant"
                    for leg in legislators:
                        if leg['type'] == 'representative':
                            rep = leg['bio']
                            rep_name = f"{rep['first_name']} {rep['last_name']}"
                            break
                    return f"{state}-{dist_num}", rep_name
    except:
        return None, None
    return None, None

def is_duplicate(email):
    filename = 'pledges.csv'
    if not os.path.isfile(filename): return False
    clean_input = email.strip().lower()
    try:
        df = pd.read_csv(filename)
        if 'Email' in df.columns:
            existing_emails = df['Email'].astype(str).str.strip().str.lower().values
            if clean_input in existing_emails: return True
        else: return False
    except: return False
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
        st.error(f"❌ Email Failed: {e}")
        return None

def save_pledge(name, email, district, rep_name):
    filename = 'pledges.csv'
    file_exists = os.path.isfile(filename)
    clean_email = email.strip().lower()
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Name', 'Email', 'District', 'Rep'])
        writer.writerow([datetime.now(), name, clean_email, district, rep_name])

# --- THE APP UI ---

st.set_page_config(page_title="The 80% Bill", page_icon="🇺🇸", layout="wide")

# --- CUSTOM THEME ---
st.markdown("""
<style>
    /* 1. FORCE MAIN BACKGROUND */
    .stApp { background-color: #F9F7F2; }
    
    /* 2. FORCE TEXT COLORS (Global Override) */
    h1, h2, h3, h4, h5, h6, p, li, span, label, .stMarkdown { 
        color: #0C2340 !important; 
    }

    /* 3. FIX INPUT BOXES */
    input[type="text"], input[type="email"], textarea {
        background-color: #ffffff !important; 
        color: #000000 !important; 
        border: 1px solid #ccc !important;
    }
    ::placeholder { color: #666666 !important; opacity: 1; }
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    div[data-baseweb="select"] span { color: #000000 !important; }

    /* 4. FIX ALL BUTTONS (Universal Selector) */
    /* We removed the '>' so this hits both Regular AND Form buttons */
    div.stButton button {
        background-color: #0C2340 !important;
        border: none !important;
        color: #ffffff !important;
    }
    
    /* Force all internal text (p tags, spans, divs) to be white */
    div.stButton button * {
        color: #ffffff !important;
    }

    /* Hover State */
    div.stButton button:hover {
        background-color: #BF0A30 !important;
        color: #ffffff !important;
    }
    div.stButton button:hover * {
        color: #ffffff !important;
    }

    /* 5. TABS */
    button[data-baseweb="tab"] { color: #0C2340 !important; }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #BF0A30 !important;
        border-bottom-color: #BF0A30 !important;
    }

    /* 6. ARTICLE BOX STYLING */
    .article-box {
        background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;
        border-left: 6px solid #0C2340; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .article-title { font-weight: 800; color: #0C2340; font-size: 20px; margin-bottom: 5px; }
    .article-desc { color: #333; font-size: 16px; margin-bottom: 12px; }
    
    .bill-link { 
        text-decoration: none; color: white !important; font-weight: bold; font-size: 14px;
        background-color: #BF0A30; padding: 8px 16px; border-radius: 5px; display: inline-block;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: all 0.2s;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    if LOGO_IMG: st.image(LOGO_IMG, use_container_width=True)
    else: st.header("🇺🇸 The 80% Bill")
    st.divider()
    st.header("Support the Project")
    st.link_button("☕ Buy me a Coffee ($5)", DONATION_LINK)
    st.divider()
    with st.expander("🕵️‍♂️ Admin"):
        if os.path.isfile('pledges.csv'):
            if st.button("⚠️ Reset Database"):
                os.remove('pledges.csv')
                st.rerun()

# --- MAIN PAGE ---
st.title("🏛️ The 80% Bill")

st.markdown(" ")
tab1, tab2, tab3 = st.tabs(["✍️ Sign the Pledge", "📊 Live Dashboard", "📜 Read the Bill"])

with tab1:
    if 'step' not in st.session_state: st.session_state.step = 1
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.step == 1:
            st.subheader("Step 1: Verify your District")
            st.info("We need your address to find your Congressional Representative.")
            search_query = st.text_input("Enter your home address:", placeholder="e.g. 123 Main St, New York, NY")
            if st.button("Find My District"):
                with st.spinner("Searching map..."):
                    results = get_osm_addresses(search_query)
                    if results:
                        st.session_state.address_options = {item['display_name']: item['display_name'] for item in results}
                        st.session_state.show_results = True
                    else: st.error("No address found. Please try again.")
            if st.session_state.get('show_results'):
                selected = st.selectbox("Confirm exact match:", list(st.session_state.address_options.keys()))
                if st.button("This is my address"):
                    district, rep = get_district(selected)
                    if district:
                        st.session_state.confirmed_address = selected
                        st.session_state.district_info = (district, rep)
                        st.session_state.step = 2
                        st.rerun()
                    else: st.error("District not found.")

        elif st.session_state.step == 2:
            dist, rep = st.session_state.district_info
            st.success(f"📍 You are in **{dist}** represented by **{rep}**.")
            with st.form("contact_form"):
                st.subheader("Step 2: Verify & Sign")
                name = st.text_input("Full Name")
                email_input = st.text_input("Email Address")
                st.caption("We will email a 4-digit code to this address.")
                if st.form_submit_button("Send Code"):
                    if name and email_input and "@" in email_input:
                        clean_email = email_input.strip().lower()
                        if is_duplicate(clean_email): st.error(f"❌ '{clean_email}' has already signed.")
                        else:
                            code = send_email_code(clean_email)
                            if code:
                                st.session_state.verification_code = code
                                st.session_state.user_details = (name, clean_email)
                                st.session_state.step = 3
                                st.rerun()
                    else: st.error("Invalid email.")

        elif st.session_state.step == 3:
            st.subheader("Step 3: Confirm Sign-up")
            st.info(f"Checking for code sent to {st.session_state.user_details[1]} (check spam if you don't see it)")
            user_code = st.text_input("Enter 4-digit code:")
            if st.button("Verify & Sign"):
                if user_code == st.session_state.verification_code:
                    name, email = st.session_state.user_details
                    dist, rep = st.session_state.district_info
                    if is_duplicate(email): st.error("❌ Already signed.")
                    else:
                        save_pledge(name, email, dist, rep)
                        st.balloons()
                        st.success("✅ PLEDGE CONFIRMED!")
                        st.link_button("❤️ Donate $5", DONATION_LINK)
                        if st.button("Start Over"):
                            st.session_state.clear()
                            st.rerun()
                else: st.error("Incorrect code.")

with tab2:
    st.header("📊 Campaign Progress")
    if os.path.isfile('pledges.csv'):
        df = pd.read_csv('pledges.csv')
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Signatures", len(df))
            c2.metric("Districts Active", df['District'].nunique())
            st.divider()
            st.bar_chart(df['District'].value_counts())
            st.dataframe(df[['Name', 'District', 'Rep']].tail(5), use_container_width=True)
        else: st.info("No signatures yet.")
    else: st.info("No signatures yet.")

with tab3:
    st.markdown("# Every single article below is supported by at least 80% of American voters.")
    
# --- CUSTOM THEME (FRESH START) ---
st.markdown("""
<style>
    /* 1. FORCE LIGHT MODE BACKGROUND (Crucial for Mobile) */
    [data-testid="stAppViewContainer"] {
        background-color: #F9F7F2;
    }
    [data-testid="stHeader"] {
        background-color: #F9F7F2; /* Hides the top bar */
    }

    /* 2. TEXT COLORS - Make everything Navy by default */
    h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown {
        color: #0C2340 !important;
    }

    /* 3. INPUT FIELDS - The "Reset" */
    /* This forces all text boxes to be white with black text, ignoring phone settings */
    input, textarea, select {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ccc !important;
        caret-color: #000000 !important; /* The typing cursor color */
    }
    /* The "Hint" text inside the box */
    ::placeholder {
        color: #666666 !important;
        opacity: 1;
    }

    /* 4. BUTTONS - Simple & High Contrast */
    /* Target every single button in the app */
    button {
        background-color: #0C2340 !important;
        border: none !important;
        transition: background-color 0.3s ease;
    }
    /* Force ALL text inside buttons to be white */
    button * {
        color: #ffffff !important;
    }
    /* Hover effect */
    button:hover {
        background-color: #BF0A30 !important;
    }

    /* 5. TABS - High Visibility */
    /* The bar under the tabs */
    [data-testid="stTabs"] {
        background-color: transparent;
    }
    /* The text inside the tabs */
    [data-testid="stMarkdownContainer"] p {
        font-weight: bold;
    }

    /* 6. ARTICLE BOXES (The Bill text) */
    .article-box {
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 8px; 
        margin-bottom: 20px;
        border-left: 6px solid #0C2340; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .article-title { 
        color: #0C2340 !important; 
        font-size: 20px; 
        font-weight: 800; 
    }
    .article-desc { 
        color: #333333 !important; 
        font-size: 16px; 
    }
    .note-text {
        color: #555555 !important;
        background-color: #eeeeee;
        padding: 8px;
        font-style: italic;
        border-radius: 4px;
    }

    /* 7. LINKS */
    a.bill-link {
        color: #ffffff !important;
        background-color: #BF0A30;
        padding: 8px 16px;
        border-radius: 4px;
        text-decoration: none;
        display: inline-block;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

    for title, desc, link, note in articles:
        note_html = f"<div class='note-text'>{note}</div>" if note else ""
        html_block = f"""<div class="article-box"><div class="article-title">{title}</div><div class="article-desc">{desc}</div>{note_html}<a href="{link}" target="_blank" class="bill-link">🏛️ Read the Bill</a></div>"""
        st.markdown(html_block, unsafe_allow_html=True)
