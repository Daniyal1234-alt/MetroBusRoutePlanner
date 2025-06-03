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
    brt = fetch_stations("BRT_Stations")    
    yellow_brt = fetch_stations("BRT_Yellow_Stations")
    G = nx.Graph()
    minimumSourceDistance = math.inf
    minimumDestinationDistance = math.inf
    for i in range(len(brt)):
        G.add_node(brt[i]['name'], pos=brt[i]['coords'], line=brt[i]['line'])
        if i>0:
            d = geodesic(brt[i]['coords'], brt[i-1]['coords']).meters
            G.add_edge(brt[i-1]['name'], brt[i]['name'], weight=d)
            distancefromsource = geodesic(brt[i]['coords'], user_current_coordinates)
            distancefromdestination = geodesic(brt[i]['coords'], user_destination_coordinates)
            if distancefromsource < minimumSourceDistance:
                minimumSourceDistance = distancefromsource
                start = brt[i]['name']
            if distancefromdestination < minimumDestinationDistance:
                minimumDestinationDistance = distancefromdestination
                destination = brt[i]['name']
            

    for i in range(len(yellow_brt)):
        G.add_node(yellow_brt[i]['name'], pos=yellow_brt[i]['coords'], line=yellow_brt[i]['line'])
        if i>0:
            d = geodesic(yellow_brt[i]['coords'], yellow_brt[i-1]['coords']).meters
            G.add_edge(yellow_brt[i-1]['name'], yellow_brt[i]['name'], weight=d)
            distancefromsource = geodesic(yellow_brt[i]['coords'], user_current_coordinates)
            distancefromdestination = geodesic(yellow_brt[i]['coords'], user_destination_coordinates)
            if distancefromsource < minimumSourceDistance:
                minimumSourceDistance = distancefromsource
                start = yellow_brt[i]['name']
            if distancefromdestination < minimumDestinationDistance:
                minimumDestinationDistance = distancefromdestination
                destination = yellow_brt[i]['name']
            
    # Interchange
    for s1 in brt:
        for s2 in yellow_brt:
            if geodesic(s1['coords'], s2['coords']).meters < 50:  # small threshold
                G.add_edge(s1['name'], s2['name'], weight=50) 

    return G, brt, yellow_brt, start, destination

def path_finding(G, start, destination, brt, yellow_brt):
    path = nx.shortest_path(G, source=start, target=destination, weight="weight")

    # Quick lookup sets for identifying the line
    brt_names = {station["name"] for station in brt}
    yellow_brt_names = {station["name"] for station in yellow_brt}

    total_distance = 0
    route_info = []

    for i, node in enumerate(path):
        # Determine which line the node belongs to
        if node in brt_names:
            line = "BRT"
        elif node in yellow_brt_names:
            line = "Yellow BRT"
        else:
            line = "Unknown"

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

    print("\n--- Route Breakdown ---")
    for segment in route_info:
        print(f"{segment['station']} - {segment['line']} - {segment['segment_distance_m']} m")

    print("\n--- Travel Summary ---")
    print(f"Total Distance: {total_distance_km:.2f} km")
    print(f"Estimated Travel Time: {travel_time_min:.1f} minutes")

    return route_info, total_distance_km, travel_time_min
