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
            node_id = f"{station['name']} ({station['line']})"  # <-- Unique node ID
            G.add_node(node_id, pos=station['coords'], line=station['line'], name=station['name'])

            if i > 0:
                prev_station = line_stations[i - 1]
                prev_node_id = f"{prev_station['name']} ({prev_station['line']})"
                d = geodesic(station['coords'], prev_station['coords']).meters
                G.add_edge(prev_node_id, node_id, weight=d)

            # Determine closest station to source and destination
            distancefromsource = geodesic(station['coords'], user_current_coordinates).meters
            distancefromdestination = geodesic(station['coords'], user_destination_coordinates).meters
            if distancefromsource < minimumSourceDistance:
                minimumSourceDistance = distancefromsource
                start = f"{station['name']} ({station['line']})"

            if distancefromdestination < minimumDestinationDistance:
                minimumDestinationDistance = distancefromdestination
                destination = f"{station['name']} ({station['line']})"
    # Add interchanges between lines
    for i in range(len(all_stations)):
        for j in range(i + 1, len(all_stations)):
            s1 = all_stations[i]
            s2 = all_stations[j]
            if s1['line'] != s2['line']:
                d = geodesic(s1['coords'], s2['coords']).meters
                if d < 500:
                    n1 = f"{s1['name']} ({s1['line']})"
                    n2 = f"{s2['name']} ({s2['line']})"
                    G.add_edge(n1, n2, weight=d)

    return G, red_brt, yellow_brt, blue_brt, green_brt, start, destination

def print_full_graph(G):
    print("\n--- All Nodes ---")
    for node in G.nodes(data=True):
        print(node)

    print("\n--- All Edges with Weights ---")
    for u, v, data in G.edges(data=True):
        print(f"{u} <--> {v} | weight = {data.get('weight', 'N/A')}")

import networkx as nx

def path_finding(G, start, destination, red_brt, yellow_brt, blue_brt, green_brt):
    def try_shortest_path(src, dst):
        try:
            return nx.shortest_path(G, source=src, target=dst, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    # Try the initial path
    path = try_shortest_path(start, destination)

    # If path not found, find nearest alternative starts
    if not path:
        print(f"No path found from '{start}' to '{destination}'. Trying closest alternative stations...")
        candidates = []
        for node in G.nodes():
            try:
                distance = nx.shortest_path_length(G, source=start, target=node, weight="weight")
                candidates.append((distance, node))
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        # Sort nodes by distance from original start
        candidates.sort()
        print(candidates)
        # Try alternate starts from closest to farthest
        for _, alt_start in candidates:
            path = try_shortest_path(alt_start, destination)
            if path:
                print(f"Found alternate path from '{alt_start}' to '{destination}'.")
                start = alt_start
                break

    if not path:
        print("❌ No valid route found from any nearby station.")
        return None, 0, 0, 0

    # Proceed as before with route breakdown
    red_brt_names = {station["name"]+" (BRT)"  for station in red_brt}
    yellow_brt_names = {station["name"]+" (BRT YELLOW)" for station in yellow_brt}
    blue_brt_names = {station["name"]+" (BRT BLUE)" for station in blue_brt}
    green_brt_names = {station["name"]+" (BRT GREEN)" for station in green_brt}
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

        if previous_line and line != previous_line:
            interchanges.append({
                "station": node,
                "from_line": previous_line,
                "to_line": line
            })
        previous_line = line
        used_lines.add(line)

        segment_distance = round(G.get_edge_data(path[i - 1], node)["weight"], 2) if i > 0 else 0.0
        total_distance += segment_distance

        route_info.append({
            "station": node,
            "line": line,
            "segment_distance_m": segment_distance
        })

    total_distance_km = total_distance / 1000
    avg_speed_kmh = 25
    travel_time_min = (total_distance_km / avg_speed_kmh) * 60 + (len(path) - 1) * 0.5

    total_wait_time = sum(line_info[line]["wait_time"] for line in used_lines if line in line_info)
    total_cost = sum(line_info[line]["cost"] for line in used_lines if line in line_info)


    return route_info, total_distance_km, travel_time_min + total_wait_time, total_cost
