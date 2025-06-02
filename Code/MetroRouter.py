import streamlit as st
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Metro Router App", layout="centered")
st.title("🗺️ Islamabad-Rawalpindi Metro Route Planner")

st.markdown("Pin your **Current Location** and **Destination** using the map or select from famous locations.")

# Sample famous locations (expand as needed)
famous_places = {
    "Select a place": None,
    "Faisal Mosque": (33.7294, 73.0387),
    "Centaurus Mall": (33.7074, 73.0519),
    "Rawalpindi Saddar": (33.5973, 73.0531),
    "Zero Point": (33.6845, 73.0479),
    "Faizabad Interchange": (33.6580, 73.0744),
    "NUST H-12": (33.6434, 72.9908),
    "Pir Wadhai Bus Terminal": (33.6231, 73.0643),
    "I-8 Markaz": (33.6846, 73.0709)
}

# Session state
if "start_coords" not in st.session_state:
    st.session_state.start_coords = None
if "end_coords" not in st.session_state:
    st.session_state.end_coords = None
if "dropping" not in st.session_state:
    st.session_state.dropping = None

# Dropdowns for popular places
col1, col2 = st.columns(2)
with col1:
    selected_start = st.selectbox("📍 Choose Current Location", list(famous_places.keys()), key="start")
    if famous_places[selected_start]:
        st.session_state.start_coords = {"lat": famous_places[selected_start][0], "lng": famous_places[selected_start][1]}
with col2:
    selected_end = st.selectbox("🏁 Choose Destination", list(famous_places.keys()), key="end")
    if famous_places[selected_end]:
        st.session_state.end_coords = {"lat": famous_places[selected_end][0], "lng": famous_places[selected_end][1]}

st.divider()

# Buttons to manually drop pins
col3, col4 = st.columns(2)
with col3:
    if st.button("🔵 Drop Current Location Manually"):
        st.session_state.dropping = "start"
with col4:
    if st.button("🟢 Drop Destination Manually"):
        st.session_state.dropping = "end"

# Set map center
center = [33.6844, 73.0479]  # default
if st.session_state.end_coords:
    center = [st.session_state.end_coords["lat"], st.session_state.end_coords["lng"]]
elif st.session_state.start_coords:
    center = [st.session_state.start_coords["lat"], st.session_state.start_coords["lng"]]

# Create map
m = folium.Map(location=center, zoom_start=12)

# Add markers if present
if st.session_state.start_coords:
    folium.Marker(
        [st.session_state.start_coords["lat"], st.session_state.start_coords["lng"]],
        tooltip="📍 Current Location",
        icon=folium.Icon(color="blue")
    ).add_to(m)

if st.session_state.end_coords:
    folium.Marker(
        [st.session_state.end_coords["lat"], st.session_state.end_coords["lng"]],
        tooltip="🏁 Destination",
        icon=folium.Icon(color="green")
    ).add_to(m)

# Show map and handle clicks
map_data = st_folium(m, width=700, height=500)

# Update coordinates if clicked
if map_data.get("last_clicked") and st.session_state.dropping:
    coords = map_data["last_clicked"]
    if st.session_state.dropping == "start":
        st.session_state.start_coords = coords
    elif st.session_state.dropping == "end":
        st.session_state.end_coords = coords
    st.session_state.dropping = None  # clear dropping flag

# Final summary
st.divider()
if st.session_state.start_coords and st.session_state.end_coords:
    st.success("✅ Locations Selected!")
    st.markdown(f"""
    - **Current Location:** `{st.session_state.start_coords["lat"]:.5f}, {st.session_state.start_coords["lng"]:.5f}`
    - **Destination:** `{st.session_state.end_coords["lat"]:.5f}, {st.session_state.end_coords["lng"]:.5f}`
    """)
