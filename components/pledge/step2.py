import streamlit as st
from utils.data import is_duplicate, save_pledge


def render_step2():
    """Step 2: name/email form and pledge submission."""
    dist, rep = st.session_state.district_info
    st.success(f"You are in **{dist}** represented by **{rep}**.")

    if st.button("Wrong District? Change it."):
        st.session_state.step = 1
        st.rerun()

    with st.form("contact_form"):
        st.subheader("Step 2: Sign the Pledge")
        name = st.text_input("Full Name")
        email_input = st.text_input("Email Address")

        if st.form_submit_button(
            "I will not vote for anyone who does not support this bill, unaltered"
        ):
            if name and email_input and "@" in email_input:
                clean_email = email_input.strip().lower()
                with st.spinner(""):
                    already_signed = is_duplicate(clean_email)
                if already_signed:
                    st.error(f"❌ '{clean_email}' has already signed.")
                else:
                    with st.spinner(""):
                        save_pledge(name, clean_email, dist, rep)
                    st.session_state.step = 3
                    st.rerun()
            else:
                st.error("Invalid email.")
