import streamlit as st
from components.shared.theme import LOGO_IMG, DONATION_LINK


def render_sidebar():
    """Render the persistent sidebar: logo and donation button."""
    with st.sidebar:
        if LOGO_IMG:
            st.image(LOGO_IMG, width="stretch")
        else:
            st.header("🇺🇸 The 80% Bill")
        st.divider()
        st.header("Support the Project")
        st.link_button("☕ Buy me a Coffee ($5)", DONATION_LINK, type="primary", width="stretch")
        st.divider()
