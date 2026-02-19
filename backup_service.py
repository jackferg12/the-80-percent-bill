import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

def save_to_vault(name, email, district, rep_name):
    vault_url = st.secrets.get("BACKUP_URL")
    if not vault_url:
        print("⚠️ BACKUP_URL not set in secrets - skipping backup")
        return False
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(spreadsheet=vault_url, worksheet="Sheet1", ttl=0)
        
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": name,
            "Email": email,
            "District": district,
            "Rep": rep_name
        }])
        
        if existing_data is None: updated_df = new_row
        else: updated_df = pd.concat([existing_data, new_row], ignore_index=True)

        conn.update(spreadsheet=vault_url, worksheet="Sheet1", data=updated_df)
        print("✅ Backup Saved.")
        return True
    except Exception as e:
        print(f"❌ VAULT FAILURE: {e}")
        return False
