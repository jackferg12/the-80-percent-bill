import streamlit as st
from components.shared.theme import inject_theme
from components.shared.sidebar import render_sidebar

st.set_page_config(
    page_title="The 80% Bill",
    page_icon="🇺🇸",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

inject_theme()
render_sidebar()

home_page   = st.Page("pages/home.py",   title="Home",            icon="🏠", default=True)
pledge_page = st.Page("pages/pledge.py", title="Sign the Pledge", icon="✍️")
bill_page   = st.Page("pages/bill.py",   title="Read the Bill",   icon="📖")

public_pages = [home_page, pledge_page, bill_page]

# Admin page is only surfaced in nav after authentication
if st.session_state.get("admin_authed"):
    admin_page = st.Page("pages/admin.py", title="Admin", icon="🔐")
    nav = st.navigation(public_pages + [admin_page], position="hidden")
else:
    nav = st.navigation(public_pages, position="hidden")

nav.run()
