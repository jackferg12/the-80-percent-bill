import streamlit as st
from components.pledge.step1 import render_step1
from components.pledge.step2 import render_step2
from components.pledge.step3 import render_step3

if "step" not in st.session_state:
    st.session_state.step = 1

st.title("The 80% Bill")
st.markdown("---")
st.info("**Pledge:** By completing this form, I state that I will not vote for anyone who does not actively support this bill.")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.session_state.step == 1:
        render_step1()
    elif st.session_state.step == 2:
        render_step2()
    elif st.session_state.step == 3:
        render_step3()
