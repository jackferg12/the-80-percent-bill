import streamlit as st
from components.shared.theme import DONATION_LINK


def render_hero():
    """Landing page hero section with CTA buttons."""
    st.title("The 80% Bill")
    st.markdown(
        '<p style="color: #4A5568; font-size: 1.1rem; margin-top: -0.5rem;">'
        "20 bills that 80%+ of Americans support. Sign the pledge."
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("✍️ Sign the Pledge")
        st.markdown(
            "Add your name. Tell your representative you will not vote for "
            "anyone who doesn't support this bill."
        )
        if st.button("Add Your Name →", type="primary", use_container_width=True):
            st.switch_page("pages/pledge.py")

    with col2:
        st.subheader("📖 Read the Bill")
        st.markdown(
            "Browse all 20 articles — each supported by 80%+ of Americans "
            "across party lines."
        )
        if st.button("Read the Bill →", use_container_width=True):
            st.switch_page("pages/bill.py")
