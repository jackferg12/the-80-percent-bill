import streamlit as st
import requests
import pandas as pd
import random
import os
import backup_service
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GEOCODIO_API_KEY = st.secrets["GEOCODIO_API_KEY"]
EMAIL_ADDRESS = "the.80.percent.bill@gmail.com"
EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
DONATION_LINK = "https://www.buymeacoffee.com/80percentbill" 

# --- ASSETS ---
def find_image(options):
    for img in options:
        if os.path.exists(img): return img
    return None
LOGO_IMG = find_image(["Gemini_Generated_Image_1dkkh41dkkh41dkk.jpg", "logo.jpg", "logo.png"])

# --- HELPER FUNCTIONS ---
def is_duplicate(email):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", usecols=[2], ttl=0)
        if df is not None and not df.empty:
            existing_emails = df.iloc[:, 0].astype(str).str.strip().str.lower().values
            return email.strip().lower() in existing_emails
    except Exception:
        return False
    return False

def save_pledge(name, email, district, rep_name):
    # 1. Backup First
    backup_service.save_to_vault(name, email, district, rep_name)

    # 2. Main Sheet
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        
        # SAFETY LOCKS
        if existing_data is None or existing_data.empty:
            st.error("⚠️ CRITICAL SAFETY LOCK: Database read returned 0 rows.")
            return False
        if len(existing_data) < 50: 
            st.error(f"⚠️ CRITICAL SAFETY LOCK: Suspiciously few rows ({len(existing_data)}).")
            return False

        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": name,
            "Email": email,
            "District": district,
            "Rep": rep_name
        }])
        
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        return True
    except Exception as e:
        st.error(f"⚠️ GOOGLE SHEETS ERROR: {e}")
        # Return True because Backup succeeded
        return True

# --- UI SETUP ---
st.set_page_config(page_title="The 80% Bill", page_icon="🇺🇸", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F9F7F2; }
    [data-testid="stHeader"] { background-color: #F9F7F2; }
    h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown { color: #0C2340 !important; }
    input, textarea, select { background-color: #ffffff !important; color: #000000 !important; border: 1px solid #ccc !important; }
    button { background-color: #0C2340 !important; border: none !important; }
    button * { color: #ffffff !important; }
    button:hover { background-color: #BF0A30 !important; }
    [data-testid="stLinkButton"] { background-color: #0C2340 !important; border: none !important; color: #ffffff !important; text-decoration: none !important; font-weight: 800 !important; }
    [data-testid="stLinkButton"] p { color: #ffffff !important; }
    [data-testid="stLinkButton"]:hover { background-color: #BF0A30 !important; }
    [data-testid="stSidebar"] { background-color: #0C2340 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] [data-testid="stLinkButton"] { background-color: #FFDD00 !important; color: #000000 !important; }
    [data-testid="stSidebar"] [data-testid="stLinkButton"] p { color: #000000 !important; }
    [data-testid="stTabs"] { background-color: transparent; }
    .article-box { background-color: #ffffff; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid #0C2340; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .article-title { color: #0C2340 !important; font-size: 20px; font-weight: 800; }
    .article-desc { color: #333333 !important; font-size: 16px; }
    .note-text { color: #555555 !important; background-color: #eeeeee; padding: 8px; font-style: italic; border-radius: 4px; }
    a.bill-link { color: #ffffff !important; background-color: #BF0A30; padding: 8px 16px; border-radius: 4px; text-decoration: none; display: inline-block; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    if LOGO_IMG: st.image(LOGO_IMG, use_container_width=True)
    else: st.header("🇺🇸 The 80% Bill")
    st.divider()
    st.header("Support the Project")
    st.link_button("☕ Buy me a Coffee ()", DONATION_LINK)

st.title("The 80% Bill")
st.markdown(" ")

tab1, tab2 = st.tabs(["Add Your Name", "Read the Bill"])

with tab1:
    if 'step' not in st.session_state: st.session_state.step = 1

    st.warning("By completing this form I am stating that I will not vote for anyone who does not actively support this bill.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # --- STEP 1: MANUAL ENTRY ---
        if st.session_state.step == 1:
            st.subheader("Step 1: Enter your District")
            st.info("Please enter your Congressional District and Representative's name.")
            
            def_dist = st.session_state.district_info[0] if 'district_info' in st.session_state else ""
            def_rep = st.session_state.district_info[1] if 'district_info' in st.session_state else ""

            manual_dist = st.text_input("District Code:", value=def_dist, placeholder="e.g. NY-14")
            manual_rep = st.text_input("Representative Name:", value=def_rep, placeholder="e.g. Alexandria Ocasio-Cortez")
            
            if st.button("Continue to Sign"):
                if manual_dist and manual_rep:
                    st.session_state.district_info = (manual_dist, manual_rep)
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.error("Please fill in both fields.")

        # --- STEP 2: SIGN (NO VERIFICATION) ---
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
                        if is_duplicate(clean_email): 
                            st.error(f"❌ '{clean_email}' has already signed.")
                        else:
                            save_pledge(name, clean_email, dist, rep)
                            st.session_state.step = 3
                            st.rerun()
                    else: st.error("Invalid email.")

        # --- STEP 3: SUCCESS ---
        elif st.session_state.step == 3:
            st.balloons()
            st.success("✅ NAME CONFIRMED! You have signed the pledge.")
            st.link_button("❤️ Donate  to help spread the word", DONATION_LINK)
            if st.button("Sign Another Person"):
                st.session_state.clear()
                st.rerun()

with tab2:
    st.markdown("# Every single article below is supported by at least 80% of American voters.")
    articles = [
        ("I. Ban Congressional Stock Trading", "Prohibits Members, their spouses, and dependent children from owning or trading individual stocks.", "https://www.congress.gov/bill/118th-congress/senate-bill/1171", None),
        ("II. End Forever Wars", "Repeal outdated authorizations (AUMFs) to return war powers to Congress.", "https://www.congress.gov/bill/118th-congress/senate-bill/316", None),
        ("III. Lifetime Lobbying Ban", "Former Members of Congress are banned for life from becoming registered lobbyists.", "https://www.congress.gov/bill/118th-congress/house-bill/1601", None),
        ("IV. Tax the Ultra-Wealthy", "Close tax loopholes and establish a minimum tax for billionaires.", "https://www.congress.gov/bill/118th-congress/house-bill/6498", None),
        ("V. Ban Corporate PACs", "Prohibit for-profit corporations from forming Political Action Committees.", "https://www.congress.gov/bill/118th-congress/house-bill/5941", "Severability Note included."),
        ("VI. Audit the Pentagon", "Require a full, independent audit to root out waste and fraud.", "https://www.congress.gov/bill/118th-congress/house-bill/2961", None),
        ("VII. Medicare Drug Negotiation", "Expands negotiation to 50 drugs/year and applies lower prices to private insurance.", "https://www.congress.gov/bill/118th-congress/house-bill/4895", "Combines H.R. 4895 and H.R. 853."),
        ("VIII. Fair Elections", "Pass the 'Freedom to Vote Act' and 'John Lewis Act'.", "https://www.congress.gov/bill/117th-congress/house-bill/5746", None),
        ("IX. Protect US Farmland", "Ban adversarial foreign governments from buying American farmland.", "https://www.congress.gov/bill/118th-congress/house-bill/9456", None),
        ("X. Ban Corporate Homes", "Tax penalty on corporations buying existing homes.", "https://www.congress.gov/bill/118th-congress/senate-bill/3402", None),
        ("XI. Fund Social Security", "Lifts the cap on wages and taxes investment income for earners over 00k.", "https://www.congress.gov/bill/118th-congress/senate-bill/1174", None),
        ("XII. Police Body Cameras", "Mandates cameras for federal officers and cuts funding for non-compliance.", "https://www.congress.gov/bill/117th-congress/house-bill/1280", None),
        ("XIII. Ban 'Dark Money'", "Overturn Citizens United (Constitutional Amendment trigger).", "https://www.congress.gov/bill/118th-congress/house-joint-resolution/54", None),
        ("XIV. Paid Family Leave", "Guarantees 12 weeks of paid leave funded by payroll insurance.", "https://www.congress.gov/bill/118th-congress/house-bill/3481", None),
        ("XV. Release Epstein Files", "Full unredacted release of documents.", "https://www.congress.gov/bill/119th-congress/house-resolution/577", None),
        ("XVI. Veterans Care Choice", "Codifies right to private care with network standards.", "https://www.congress.gov/bill/118th-congress/house-bill/8371", None),
        ("XVII. The DISCLOSE Act", "Immediate disclosure of donors over 0k.", "https://www.congress.gov/bill/118th-congress/senate-bill/512", None),
        ("XVIII. Close Loopholes", "Reclassifies Carried Interest as ordinary income.", "https://www.congress.gov/bill/118th-congress/senate-bill/4123", None),
        ("XIX. Right to Repair", "Guarantees access to parts/manuals for cars and electronics.", "https://www.congress.gov/bill/118th-congress/house-bill/906", None),
        ("XX. Ban Junk Fees", "Requires all-in price disclosure.", "https://www.congress.gov/bill/118th-congress/house-bill/2463", None)
    ]
    for title, desc, link, note in articles:
        note_html = f"<div class='note-text'>{note}</div>" if note else ""
        html_block = f"""<div class="article-box"><div class="article-title">{title}</div><div class="article-desc">{desc}</div>{note_html}<a href="{link}" target="_blank" class="bill-link">🏛️ Read the Bill</a></div>"""
        st.markdown(html_block, unsafe_allow_html=True)
