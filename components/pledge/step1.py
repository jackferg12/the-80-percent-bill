import streamlit as st
from streamlit_searchbox import st_searchbox
from utils.geo import get_osm_addresses, get_district


def render_step1():
    """Step 1: address lookup and/or manual district entry."""
    st.subheader("Step 1: Enter your District")
    st.markdown("**Enter your address to look up this info:**")

    def _address_search(searchterm: str):
        return [
            r.get("display_name")
            for r in get_osm_addresses(searchterm)
            if r.get("display_name")
        ][:6]

    def _on_address_select(selected_address):
        if selected_address:
            with st.spinner(""):
                district, rep = get_district(selected_address)
            if district and rep:
                st.session_state.district_info = (district, rep)
                st.session_state.district_input = district
                st.session_state.rep_input = rep
                st.session_state.address_just_populated = True
                st.session_state.pop("address_lookup_error", None)
                st.rerun()
            else:
                st.session_state.address_lookup_error = "Could not find congressional district."

    st_searchbox(
        _address_search,
        key="address_searchbox",
        placeholder="Type to search (addresses appear below as you type)",
        debounce=600,
        clear_on_submit=False,
        submit_function=_on_address_select,
    )

    if st.session_state.get("address_lookup_error"):
        st.error(st.session_state.pop("address_lookup_error"))

    if st.session_state.get("address_just_populated"):
        st.success("✓ **Filled in!** Verify your district and representative below, then click **Continue to Sign**.")
        del st.session_state["address_just_populated"]

    st.markdown("---")
    st.markdown("**Or enter manually:**")

    if "district_input" not in st.session_state:
        st.session_state.district_input = (
            st.session_state.district_info[0] if "district_info" in st.session_state else ""
        )
    if "rep_input" not in st.session_state:
        st.session_state.rep_input = (
            st.session_state.district_info[1] if "district_info" in st.session_state else ""
        )

    manual_dist = st.text_input("District Code:", placeholder="e.g. NY-14", key="district_input")
    manual_rep = st.text_input(
        "Representative Name:", placeholder="e.g. Alexandria Ocasio-Cortez", key="rep_input"
    )

    if st.button("Continue to Sign", key="continue_manual"):
        if manual_dist and manual_rep:
            st.session_state.district_info = (manual_dist, manual_rep)
            st.session_state.step = 2
            st.rerun()
        else:
            st.error("Please fill in both District Code and Representative Name.")
