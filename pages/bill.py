import streamlit as st
from components.bill.articles import render_articles

st.title("The 80% Bill")
st.markdown(
    "### Every article below is supported by at least 80% of American voters.\n\n"
    "Browse the bills, read the details, and click through to Congress.gov for the full legislation."
)

render_articles()
