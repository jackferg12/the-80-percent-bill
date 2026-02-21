import streamlit as st
from components.shared.theme import DONATION_LINK


def render_step3():
    """Step 3: success confirmation after pledge is saved."""
    st.balloons()
    st.success("**Thank you!** Your name has been added to the pledge.")
    st.markdown("")
    st.markdown(
        f'<a href="{DONATION_LINK}" target="_blank" rel="noopener noreferrer" class="donate-success-btn">'
        "❤️ Donate $5 to help spread the word</a>",
        unsafe_allow_html=True,
    )
    st.markdown("")
    if st.button("Sign Another Person"):
        st.session_state.clear()
        st.rerun()
