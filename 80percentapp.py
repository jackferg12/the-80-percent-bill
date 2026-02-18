
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
        
        # --- CRITICAL SAFETY UPGRADE ---
        # If the sheet returns EMPTY or very few rows, we assume a Read Error.
        # Since you already have 150+ signatures, we set the floor to 50.
        if existing_data is None or existing_data.empty:
            st.error("⚠️ CRITICAL SAFETY LOCK: Database read returned 0 rows. Save aborted to protect data.")
            return False
            
        if len(existing_data) < 50: 
            st.error(f"⚠️ CRITICAL SAFETY LOCK: Database returned suspiciously few rows ({len(existing_data)}). Save aborted to protect data.")
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
        st.error(f"⚠️ GOOGLE SHEETS ERROR: {e}")
        # Return True anyway because we know the Backup Vault has the data
        return True
        
# --- THE APP UI ---

st.set_page_config(page_title="The 80% Bill", page_icon="🇺🇸", layout="wide")

# --- CUSTOM THEME (FRESH START) ---
st.markdown("""
<style>
    /* 1. FORCE LIGHT MODE BACKGROUND */
    [data-testid="stAppViewContainer"] {
        background-color: #F9F7F2;
    }
    [data-testid="stHeader"] {
        background-color: #F9F7F2; 
    }

    /* 2. TEXT COLORS */
    h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown {
        color: #0C2340 !important;
    }

    /* 3. INPUT FIELDS */
    input, textarea, select {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ccc !important;
        caret-color: #000000 !important;
    }
    ::placeholder {
        color: #666666 !important;
        opacity: 1;
    }

    /* 4. BUTTONS (Standard Buttons) */
    button {
        background-color: #0C2340 !important;
        border: none !important;
        transition: background-color 0.3s ease;
    }
    button * {
        color: #ffffff !important;
    }
    button:hover {
        background-color: #BF0A30 !important;
    }

    /* Main Page Buttons (Navy) */
    [data-testid="stLinkButton"] {
        background-color: #0C2340 !important;
        color: #ffffff !important;
    }
    [data-testid="stLinkButton"] p { color: #ffffff !important; }

    /* SIDEBAR ONLY OVERRIDE (Yellow) */
    [data-testid="stSidebar"] [data-testid="stLinkButton"] {
        background-color: #FFDD00 !important; /* Bright Yellow */
        color: #000000 !important;            /* Black Text */
    }
    [data-testid="stSidebar"] [data-testid="stLinkButton"] p {
        color: #000000 !important;            /* Force Black Text */
    }

    /* --- SIDEBAR THEME --- */
    
    /* 1. Make the Sidebar Background Navy Blue */
    [data-testid="stSidebar"] {
        background-color: #0C2340 !important;
    }

    /* 2. Make All Sidebar Text White (Headers & Paragraphs) */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }

    /* 3. Sidebar Divider Line (Make it white/light so it shows up) */
    [data-testid="stSidebar"] hr {
        border-color: #ffffff !important;
    }
    
    /* 4. Sidebar Buttons (Keep them Yellow/Black for contrast) */
    [data-testid="stSidebar"] [data-testid="stLinkButton"] {
        background-color: #FFDD00 !important;
        color: #000000 !important;
    }
    [data-testid="stSidebar"] [data-testid="stLinkButton"] p {
        color: #000000 !important;
    }

    /* 6. TABS */
    [data-testid="stTabs"] {
        background-color: transparent;
    }
    [data-testid="stMarkdownContainer"] p {
        font-weight: bold;
    }

    /* 7. ARTICLE BOXES */
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
    /* Custom Bill Links */
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

# --- SIDEBAR ---
with st.sidebar:
    if LOGO_IMG: st.image(LOGO_IMG, use_container_width=True)
    else: st.header("🇺🇸 The 80% Bill")
    st.divider()
    st.header("Support the Project")
    st.link_button("☕ Buy me a Coffee ($5)", DONATION_LINK)
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
st.markdown(" ")

tab1, tab2 = st.tabs(["Add Your Name", "Read the Bill"])

with tab1:
    if 'step' not in st.session_state: st.session_state.step = 1

    st.warning("By completing this form I am stating that I will not vote for anyone who does not actively support this bill.")
    
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
            st.success(f"You are in **{dist}** represented by **{rep}**.")
            with st.form("contact_form"):
                st.subheader("Step 2: Verify & Sign")
                name = st.text_input("Full Name")
                email_input = st.text_input("Email Address")
                st.caption("We will email a 4-digit code to this address.")
                
                if st.form_submit_button("I will not vote for anyone who does not support this bill, unaltered"):
                    if name and email_input and "@" in email_input:
                        clean_email = email_input.strip().lower()
                        if is_duplicate(clean_email): 
                            st.error(f"❌ '{clean_email}' has already signed.")
                        else:
                            # TRY TO SEND EMAIL
                            code = send_email_code(clean_email)
                            
                            if code:
                                # SUCCESS: Normal Verification Flow
                                st.session_state.verification_code = code
                                st.session_state.user_details = (name, clean_email)
                                st.session_state.step = 3
                                st.rerun()
                            else:
                                # FAILURE (Limit Hit): EMERGENCY BYPASS
                                # If email fails, we sign them anyway so we don't lose the user.
                                save_pledge(name, clean_email, dist, rep)
                                st.balloons()
                                st.success("✅ High traffic detected! We skipped email verification and added your name.")
                                st.link_button("❤️ Donate $5 to help spread the word", DONATION_LINK)
                                
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
                        st.success("✅ NAME CONFIRMED!")
                        st.link_button("❤️ Donate $5 to help spread the word", DONATION_LINK)
                        if st.button("Start Over"):
                            st.session_state.clear()
                            st.rerun()
                else: st.error("Incorrect code.")
                    
with tab2:
    st.markdown("# Every single article below is supported by at least 80% of American voters.")
    
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
