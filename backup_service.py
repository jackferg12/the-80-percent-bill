import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

def save_to_vault(name, email, district, rep_name):
    """
    Saves a signature to the SECURE VAULT sheet.
    This runs independently of the main sheet.
    """
    try:
        # 1. Get the Backup URL from Secrets
        vault_url = st.secrets["BACKUP_URL"]
        
        # 2. Establish Connection
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 3. Read the Vault
        existing_data = conn.read(spreadsheet=vault_url, worksheet="Sheet1", ttl=0)
        
        # 4. Create New Row
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": name,
            "Email": email,
            "District": district,
            "Rep": rep_name
        }])
        
        # 5. Safety Logic
        if existing_data is None:
             updated_df = new_row
        else:
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            if len(updated_df) < len(existing_data):
                print("⚠️ VAULT ERROR: Attempted overwrite prevented.")
                return False

        # 6. Update the Vault
        conn.update(spreadsheet=vault_url, worksheet="Sheet1", data=updated_df)
        print("✅ Secure Backup Saved.")
        return True

    except Exception as e:
        print(f"❌ VAULT FAILURE: {e}")
        return False
