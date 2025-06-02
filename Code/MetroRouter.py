import streamlit as st
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Metro Router App", layout="centered")
st.title("🗺️ Islamabad-Rawalpindi Metro Route Planner")

st.markdown("""
Use the buttons below to pin your **Current Location** and **Destination** on the map.
""")

# Session state to keep pins between reruns
if "start_coords" not in st.session_state:
    st.session_state.start_coords = None
if "end_coords" not in st.session_state:
    st.session_state.end_coords = None

# Drop pin buttons
col1, col2 = st.columns(2)
with col1:
    drop_start = st.button("📍 Drop Current Location")
with col2:
    drop_end = st.button("🏁 Drop Destination")

# Setup base map
m = folium.Map(location=[33.6844, 73.0479], zoom_start=12)

# Handle pin drop logic
if drop_start:
    st.info("Click on the map to set your CURRENT location.")
    st.session_state.dropping = "start"
elif drop_end:
    st.info("Click on the map to set your DESTINATION.")
    st.session_state.dropping = "end"

# Display the folium map and capture user click
map_data = st_folium(m, width=700, height=500)

# If clicked and a drop is active
if map_data.get("last_clicked") and "dropping" in st.session_state:
    coords = map_data["last_clicked"]
    if st.session_state.dropping == "start":
        st.session_state.start_coords = coords
    elif st.session_state.dropping == "end":
        st.session_state.end_coords = coords
    st.session_state.dropping = None  # Reset

# Re-render pins if already dropped
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

# Redraw map with pins
st_folium(m, width=700, height=500)

# Show results
st.markdown("---")
if st.session_state.start_coords and st.session_state.end_coords:
    st.success("✅ Coordinates captured!")
    st.write("**Current Location:**", st.session_state.start_coords)
    st.write("**Destination:**", st.session_state.end_coords)
