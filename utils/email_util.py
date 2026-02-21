import streamlit as st
import smtplib
import random
from email.mime.text import MIMEText

EMAIL_ADDRESS = "the.80.percent.bill@gmail.com"


def send_email_code(to_email):
    """Send a 4-digit verification code. Returns the code, or None on failure."""
    code = str(random.randint(1000, 9999))
    try:
        password = st.secrets["EMAIL_PASSWORD"]
        msg = MIMEText(f"Your 80% Pledge verification code is: {code}")
        msg["Subject"] = "Verification Code - The 80% Pledge"
        msg["From"] = f"The 80% Pledge <{EMAIL_ADDRESS}>"
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, password)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        return code
    except Exception as e:
        # Silent failure — caller decides how to handle None
        print(f"Email failed (likely limit hit): {e}")
        return None
