import streamlit as st
from streamlit_folium import st_folium
import folium
import Routing  # Your backend file
import pandas as pd

st.set_page_config(page_title="Metro Router App", layout="centered")
st.title("🗺️ Islamabad-Rawalpindi Metro Route Planner")

st.markdown("Pin your **Current Location** and **Destination** using the map or select from famous locations.")

# --- Famous Places ---
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

# --- Session State ---
for k in ["start_coords", "end_coords", "dropping"]:
    if k not in st.session_state:
        st.session_state[k] = None

# --- Dropdown for famous locations ---
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

# --- Manual Location Drop Buttons ---
col3, col4 = st.columns(2)
with col3:
    if st.button("🔵 Drop Current Location Manually"):
        st.session_state.dropping = "start"
with col4:
    if st.button("🟢 Drop Destination Manually"):
        st.session_state.dropping = "end"

# --- Initialize Map ---
center = [33.6844, 73.0479]
if st.session_state.end_coords:
    center = [st.session_state.end_coords["lat"], st.session_state.end_coords["lng"]]
elif st.session_state.start_coords:
    center = [st.session_state.start_coords["lat"], st.session_state.start_coords["lng"]]

m = folium.Map(location=center, zoom_start=12)

# --- Drop pins manually if map is clicked ---
map_data = st_folium(m, width=700, height=500)
if map_data.get("last_clicked") and st.session_state.dropping:
    coords = map_data["last_clicked"]
    if st.session_state.dropping == "start":
        st.session_state.start_coords = coords
    elif st.session_state.dropping == "end":
        st.session_state.end_coords = coords
    st.session_state.dropping = None

# --- Route Planning ---
st.divider()
if st.session_state.start_coords and st.session_state.end_coords:
    st.success("✅ Locations Selected!")
    st.markdown(f"""
    - **Current Location:** `{st.session_state.start_coords["lat"]:.5f}, {st.session_state.start_coords["lng"]:.5f}`
    - **Destination:** `{st.session_state.end_coords["lat"]:.5f}, {st.session_state.end_coords["lng"]:.5f}`
    """)

    user_current_coordinates = (
        st.session_state.start_coords["lat"],
        st.session_state.start_coords["lng"]
    )
    user_destination_coordinates = (
        st.session_state.end_coords["lat"],
        st.session_state.end_coords["lng"]
    )

    G, red_brt, yellow_brt, blue_brt, green_brt, start, destination = Routing.graph_maker(user_current_coordinates, user_destination_coordinates)
    route_info, total_distance_km, travel_time_min, total_cost = Routing.path_finding(G, start, destination, red_brt, yellow_brt, blue_brt, green_brt)
    st.write("Graph nodes:", list(G.nodes(data=True))[:5])  # Preview first 5 nodes
    st.write("Red BRT: ", red_brt)
    # --- Show all stops on map ---
    def plot_stops(line_stops, color):
        for stop in line_stops:
            stop_upper = stop["name"].upper()
            if stop_upper not in G.nodes:
                st.warning(f"🚫 Stop '{stop}' not found in graph!")
                continue
            if "pos" not in G.nodes[stop_upper]:
                st.warning(f"🚫 Stop '{stop}' has no 'pos' attribute!")
                continue
            lat, lon = G.nodes[stop_upper]["pos"]
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color=color,
                fill=True,
                fill_opacity=0.8,
                tooltip=stop["name"].title(),  # cleaner display
            ).add_to(m)


    plot_stops(red_brt, "red")
    plot_stops(yellow_brt, "orange")
    plot_stops(blue_brt, "blue")
    plot_stops(green_brt, "green")

    # --- Add current and destination markers ---
    folium.Marker(
        location=user_current_coordinates,
        tooltip="📍 Current Location",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    folium.Marker(
        location=user_destination_coordinates,
        tooltip="🏁 Destination",
        icon=folium.Icon(color="green")
    ).add_to(m)

    # --- Draw travel path ---
    coords_map = [G.nodes[stop["station"]]["pos"] for stop in route_info]
    folium.PolyLine(coords_map, color="red", weight=5, tooltip="Route Path").add_to(m)

    # --- Draw dashed lines for walking paths ---
    first_station_coords = coords_map[0]
    if user_current_coordinates != first_station_coords:
        folium.PolyLine([user_current_coordinates, first_station_coords], color="black", dash_array="5,5", tooltip="Walk to Start").add_to(m)

    last_station_coords = coords_map[-1]
    if user_destination_coordinates != last_station_coords:
        folium.PolyLine([last_station_coords, user_destination_coordinates], color="black", dash_array="5,5", tooltip="Walk to Destination").add_to(m)

    # --- Path Summary ---
    st.markdown("### 📍 Route Path (Station - Line)")
    for i, segment in enumerate(route_info):
        st.write(f"{i+1}. {segment['station']} - {segment['line']}")

    # --- Travel Summary ---
    st.markdown("### 🧾 Travel Summary")
    st.write(f"**Total Distance:** {total_distance_km:.2f} km")
    st.write(f"**Estimated Travel Time:** {travel_time_min:.1f} minutes")
    st.write(f"**Estimated Cost:** {total_cost} PKR")

    # --- Final Map Display ---
    st.markdown("### 🗺️ Route on Map")
    st_folium(m, width=700, height=500)
