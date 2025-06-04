import networkx as nx
import psycopg2 
from shapely import wkb
from geopy.distance import geodesic
import math as math
#Connection to DB
conn = psycopg2.connect(
    dbname="MetroBusRoute",
    user="postgres",
    password="dani",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()
user_current_coordinates = (33.64340, 72.99080)
user_destination_coordinates = (33.66342, 73.08410)

#Fetching the tables
def fetch_stations(tablename=None):
    if tablename is None:
        raise ValueError("Table name cannot be null")
    cursor.execute(f'SELECT id, sta_name,ST_Y(geom), ST_X(geom), line_code FROM "{tablename}" ORDER BY id;')
    return [
        {
            "id": row[0],
            "name": row[1],
            "coords": (row[2], row[3]), # Latitude, Longitude
            "line": row[4]
        } for row in cursor.fetchall()
    ]


def graph_maker(user_current_coordinates, user_destination_coordinates):
    start = ""
    destination = ""
    red_brt = fetch_stations("BRT_Stations")    
    yellow_brt = fetch_stations("BRT_Yellow_Stations")
    blue_brt = fetch_stations("BRT_Blue_Stations")
    green_brt = fetch_stations("BRT_Green_Stations")
    all_stations = red_brt + yellow_brt + blue_brt + green_brt

    G = nx.Graph()
    minimumSourceDistance = math.inf
    minimumDestinationDistance = math.inf

    # Add nodes and edges for each line
    for line_stations in [red_brt, yellow_brt, blue_brt, green_brt]:
        for i in range(len(line_stations)):
            station = line_stations[i]
            G.add_node(station['name'], pos=station['coords'], line=station['line'])
            if i > 0:
                prev_station = line_stations[i - 1]
                d = geodesic(station['coords'], prev_station['coords']).meters
                G.add_edge(prev_station['name'], station['name'], weight=d)
            # Determine closest station to source and destination
            distancefromsource = geodesic(station['coords'], user_current_coordinates).meters
            distancefromdestination = geodesic(station['coords'], user_destination_coordinates).meters
            if distancefromsource < minimumSourceDistance:
                minimumSourceDistance = distancefromsource
                start = station['name']
            if distancefromdestination < minimumDestinationDistance:
                minimumDestinationDistance = distancefromdestination
                destination = station['name']

    # Add interchanges between lines
    for i in range(len(all_stations)):
        for j in range(i + 1, len(all_stations)):
            s1 = all_stations[i]
            s2 = all_stations[j]
            if s1['line'] != s2['line']:
                if geodesic(s1['coords'], s2['coords']).meters < 50:
                    G.add_edge(s1['name'], s2['name'], weight=50)  # small threshold

    return G, red_brt, yellow_brt, blue_brt, green_brt, start, destination


def path_finding(G, start, destination, red_brt, yellow_brt, blue_brt, green_brt):
    path = nx.shortest_path(G, source=start, target=destination, weight="weight")

    # Quick lookup sets for identifying the line
    red_brt_names = {station["name"] for station in red_brt}
    yellow_brt_names = {station["name"] for station in yellow_brt}
    blue_brt_names = {station["name"] for station in blue_brt}
    green_brt_names = {station["name"] for station in green_brt}

    # Line-specific information
    line_info = {
        "Red BRT": {"wait_time": 2.5, "cost": 30},
        "Yellow BRT": {"wait_time": 5, "cost": 100},
        "Blue BRT": {"wait_time": 10, "cost": 100},
        "Green BRT": {"wait_time": 10, "cost": 100},
        "Unknown": {"wait_time": 0, "cost": 0}
    }

    total_distance = 0
    route_info = []
    used_lines = set()
    previous_line = None
    interchanges = []

    for i, node in enumerate(path):
        # Determine which line the node belongs to
        if node in red_brt_names:
            line = "Red BRT"
        elif node in yellow_brt_names:
            line = "Yellow BRT"
        elif node in blue_brt_names:
            line = "Blue BRT"
        elif node in green_brt_names:
            line = "Green BRT"
        else:
            line = "Unknown"

        # Check for line change
        if previous_line and line != previous_line:
            interchanges.append({
                "station": node,
                "from_line": previous_line,
                "to_line": line
            })
        previous_line = line
        used_lines.add(line)

        # Distance from previous node
        if i > 0:
            edge_data = G.get_edge_data(path[i - 1], node)
            segment_distance = round(edge_data["weight"], 2)
        else:
            segment_distance = 0.0

        total_distance += segment_distance

        route_info.append({
            "station": node,
            "line": line,
            "segment_distance_m": segment_distance
        })

    total_distance_km = total_distance / 1000  # convert to km
    avg_speed_kmh = 25
    travel_time_hr = total_distance_km / avg_speed_kmh
    travel_time_min = travel_time_hr * 60
    travel_time_min += (len(path) - 1) * 0.5  # 30 seconds stop at each station

    # Calculate total waiting time and cost
    total_wait_time = sum([line_info[line]["wait_time"] for line in used_lines if line in line_info])
    total_cost = sum([line_info[line]["cost"] for line in used_lines if line in line_info])

    print("\n--- Route Breakdown ---")
    for segment in route_info:
        print(f"{segment['station']} - {segment['line']} - {segment['segment_distance_m']} m")

    print("\n--- Interchanges ---")
    for interchange in interchanges:
        print(f"Interchange at {interchange['station']}: {interchange['from_line']} -> {interchange['to_line']}")

    print("\n--- Travel Summary ---")
    print(f"Total Distance: {total_distance_km:.2f} km")
    print(f"Estimated Travel Time: {travel_time_min + total_wait_time:.1f} minutes (including waiting time)")
    print(f"Estimated Waiting Time: {total_wait_time:.1f} minutes")
    print(f"Estimated Cost: {total_cost} PKR")

    return route_info, total_distance_km, travel_time_min + total_wait_time, total_cost
