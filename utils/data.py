import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import backup_service


def is_duplicate(email):
    """Return True if the email already exists in the main Google Sheet."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", usecols=[2], ttl=0)
        if df is not None and not df.empty:
            existing = df.iloc[:, 0].astype(str).str.strip().str.lower().values
            return email.strip().lower() in existing
    except Exception:
        return False
    return False


def save_pledge(name, email, district, rep_name):
    """Save a pledge to backup vault then to the main Google Sheet. Returns True on success."""
    # 1. Backup first — runs blindly so data is never lost if the main sheet fails
    backup_service.save_to_vault(name, email, district, rep_name)

    # 2. Save to main public sheet
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)

        # CRITICAL SAFETY: abort if sheet read returned nothing
        if existing_data is None or existing_data.empty:
            st.error("⚠️ CRITICAL SAFETY LOCK: Database read returned 0 rows. Save aborted to protect data.")
            return False

        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Name": name,
            "Email": email,
            "District": district,
            "Rep": rep_name,
        }])
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)

        # ANTI-WIPE LOCK: never allow the row count to decrease
        if len(updated_df) < len(existing_data):
            st.error(f"⚠️ SAFETY LOCK: Attempted to delete data. (Old: {len(existing_data)}, New: {len(updated_df)})")
            return False

        conn.update(worksheet="Sheet1", data=updated_df)
        return True

    except Exception as e:
        err = str(e).lower()
        if any(k in err for k in ("permission", "403", "credentials", "unauthorized")):
            st.error(
                "⚠️ Google Sheets write failed (likely read-only connection). "
                "To save pledges, use Service Account auth—see SECRETS_SETUP.md"
            )
        else:
            st.error(f"⚠️ GOOGLE SHEETS ERROR: {e}")
        return False


def get_pledge_count():
    """Return the total number of pledges, or None on error."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=60)
        if df is not None:
            return len(df)
    except Exception:
        pass
    return None


def get_all_pledges():
    """Return the full pledge DataFrame, or None on error."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(worksheet="Sheet1", ttl=0)
    except Exception:
        return None
