import streamlit as st
import requests


@st.cache_data(ttl=300, show_spinner=False)
def get_osm_addresses(search_term):
    """Fetch up to 6 address suggestions from OpenStreetMap Nominatim for US addresses."""
    if not search_term or len(search_term.strip()) < 3:
        return []
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "The80PercentPledge/1.0"}
    params = {"q": search_term, "format": "json", "limit": 6, "countrycodes": "us", "addressdetails": 1}
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return []
    return []


def get_district(address):
    """Use Geocodio API to convert address to congressional district and representative."""
    if not address:
        return None, None
    api_key = st.secrets["GEOCODIO_API_KEY"]
    url = "https://api.geocod.io/v1.7/geocode"
    params = {"q": address, "fields": "cd", "api_key": api_key}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                data = results[0]
                fields = data.get("fields", {})
                if "congressional_districts" in fields:
                    dist_data = fields["congressional_districts"][0]
                    state = data.get("address_components", {}).get("state", "")
                    dist_num = dist_data.get("district_number")
                    if state is not None and dist_num is not None:
                        legislators = dist_data.get("current_legislators", [])
                        rep_name = "Vacant"
                        for leg in legislators:
                            if leg.get("type") == "representative":
                                rep = leg.get("bio", {})
                                rep_name = f"{rep.get('first_name', '')} {rep.get('last_name', '')}".strip()
                                break
                        return f"{state}-{dist_num}", rep_name
    except Exception:
        pass
    return None, None
