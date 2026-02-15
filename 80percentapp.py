
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
    
# FORMAT: (Title, Description, Link, Optional_Note)
    articles = [

        (
            "I. Ban Congressional Stock Trading", 
            "Prohibits Members, their spouses, and dependent children from owning or trading individual stocks. Requires full divestment or a qualified blind trust.", 
            "https://www.congress.gov/bill/118th-congress/senate-bill/1171", 
            "Note: We selected the ETHICS Act (S. 1171) because it is the 'strongest' version, explicitly closing the 'spouse loophole' and banning ownership entirely."
        ),
        ("II. End Forever Wars", "Repeal outdated authorizations (AUMFs) to return war powers to Congress.", "https://www.congress.gov/bill/118th-congress/senate-bill/316", None),
        ("III. Lifetime Lobbying Ban", "Former Members of Congress are banned for life from becoming registered lobbyists.", "https://www.congress.gov/bill/118th-congress/house-bill/384", None),
        ("IV. Tax the Ultra-Wealthy", "Close tax loopholes and establish a minimum tax for billionaires.", "https://www.congress.gov/bill/118th-congress/house-bill/6498", None),
        (
            "V. Ban Corporate PACs", 
            "Prohibit for-profit corporations from forming Political Action Committees.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/4799", 
            "Note: This legislation includes a 'severability clause.' If the Supreme Court strikes down this specific ban, the rest of the 80% Bill remains law."
        ),
        ("VI. Audit the Pentagon", "The Pentagon has never passed an audit. Require a full, independent audit to root out waste and fraud.", "https://www.congress.gov/bill/118th-congress/house-bill/2961", None),
        (
            "VII. Medicare Drug Negotiation", 
            "1. H.R. 4895: Expands negotiation to 50 drugs/year and applies lower prices to private insurance.\n2. H.R. 853: Closes the 'Orphan Drug' loophole.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/4895", 
            "Note: This entry combines two bills to protect ALL Americans (not just seniors) and stop pharma from gaming the 'rare disease' system."
        ),
        (
            "VIII. Fair Elections & End Gerrymandering", 
            "Pass the 'Freedom to Vote Act' to ban partisan gerrymandering and the 'John Lewis Act' to restore the Voting Rights Act.", 
            "https://www.congress.gov/bill/117th-congress/house-bill/5746", 
            "Note: These bills ban politicians from picking their voters (gerrymandering) and protect every eligible voter from suppression."
        ),
        (
            "IX. Protect US Farmland", 
            "Ban foreign ADVERSARY governments from buying strategic farmland. Includes a 'Beneficial Ownership' registry to stop shell companies.", 
            "https://www.congress.gov/bill/118th-congress/senate-bill/618", 
            "Note: Strictly targets governments (China, Russia, Iran, NK). Explicitly protects lawful US permanent residents (Green Card holders)."
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
            "https://www.congress.gov/bill/118th-congress/senate-joint-resolution/4", 
            "Severability Note: This clause overturns *Citizens United*, but we acknowledge it will be struck down by the Court unless this bill passes with the votes required to amend the Constitution (2/3rds)."
        ),
        (
            "XIV. Paid Family Leave", 
            "Guarantees 12 weeks of paid leave funded by a payroll insurance fund. Explicitly prohibits firing workers (of any company size) for taking this leave.", 
            "https://www.congress.gov/bill/118th-congress/house-bill/3481", 
            None
        ),
        (
            "XV. Release the Epstein Files", 
            "Mandates the release of all documents. Explicitly bans redactions of perpetrator names while strictly protecting the identities of underage victims.", 
            "https://www.congress.gov/bill/118th-congress/senate-bill/2557", 
            "Note: We endorse the version that strips 'Privacy' protections for anyone accused of a crime, closing the loophole for powerful figures."
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
            "https://www.congress.gov/bill/118th-congress/house-bill/1068", 
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
