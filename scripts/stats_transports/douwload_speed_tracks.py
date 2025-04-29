import pandas as pd
import json
import geopandas as gpd
from shapely.geometry import LineString, mapping, Point
import networkx as nx
import scipy.spatial
from geopy.distance import geodesic
from collections import defaultdict

# ——————————————————————————————————————————————
# Параметры
CSV_PATH               = '../../sources/current_route/current_route.csv'
ROADS_SHP_PATH         = '../../sources/UDS/Граф Иркутск_link.SHP'
OUTPUT_GEOJSON         = 'segments_yellow_red_on_roads.geojson'
MAX_SEGMENT_DISTANCE_M = 500      # м: макс. «пробег» между соседними точками
IQR_MULTIPLIER         = 1.5      # для IQR-фильтра выбросов по скорости
# ——————————————————————————————————————————————

# 1) Загрузка и предобработка GPS-данных
df = pd.read_csv(CSV_PATH, sep=';', low_memory=False)
df = df.dropna(subset=['lat','lon','speed','signal_time'])
df['signal_time'] = pd.to_datetime(df['signal_time'])
df = df.sort_values(['uuid','signal_time']).reset_index(drop=True)

# переводим скорость в km/h и фильтруем выбросы по IQR
df['speed_kmh'] = df['speed'] * 3.6
Q1 = df['speed_kmh'].quantile(0.25)
Q3 = df['speed_kmh'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - IQR_MULTIPLIER * IQR
upper = Q3 + IQR_MULTIPLIER * IQR
df = df[(df['speed_kmh'] >= lower) & (df['speed_kmh'] <= upper)].reset_index(drop=True)

df.rename(columns={'route': 'route_number'}, inplace=True)
# Создаём вложенную структуру: route -> uuid -> средняя скорость
nested_routes = defaultdict(dict)
max_speed = 0

for (route, uuid), group in df.groupby(['route_number', 'uuid']):
    mean_speed = group['speed_kmh'].mean()
    max_speed = max(max_speed, mean_speed)
    nested_routes[str(route)][str(uuid)] = {
        'speed': round(mean_speed, 2)
    }

# Финальная структура с max_speed_kmh и данными по маршрутам
final_output = {
    "max_speed_kmh": round(max_speed, 2),
    "routes": nested_routes
}

# Сохраняем в JSON
with open('route_uuid_avg_speeds.json', 'w', encoding='utf-8') as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

print("JSON со средней скоростью по маршрутам и UUID сохранён в «route_uuid_avg_speeds.json»")
# средняя и «половинчатая» скорости (km/h)
avg_speed_kmh = df['speed_kmh'].mean()
mid_speed_kmh = avg_speed_kmh / 2

def speed_color_kmh(v_mps):
    v = v_mps * 3.6
    if v >= avg_speed_kmh:
        return 'green'
    elif v >= mid_speed_kmh:
        return 'yellow'
    else:
        return 'red'

# 2) Загрузка графа дорог и построение NetworkX-графа
roads = gpd.read_file(ROADS_SHP_PATH).to_crs(epsg=4326)

def build_graph(roads_gdf):
    G = nx.Graph()
    for geom in roads_gdf.geometry:
        if geom.geom_type == 'LineString':
            coords = list(geom.coords)
            for a,b in zip(coords, coords[1:]):
                G.add_edge(a, b,
                           weight=Point(a).distance(Point(b)),
                           geometry=LineString([a,b]))
    return G

G_roads = build_graph(roads)

# KDTree для быстрого поиска ближайшей вершины
nodes = list(G_roads.nodes)
nodes_coords = [(lon, lat) for lon, lat in nodes]  # граф хранит (lon,lat)
kdtree = scipy.spatial.KDTree(nodes_coords)

def nearest_graph_node(lat, lon):
    # возвращает граф-узел (lon,lat) ближайший к (lat,lon)
    _, idx = kdtree.query((lon, lat))
    return nodes[idx]

# 3) Формирование GeoJSON-сегментов по дорогам
features = []
for uid, grp in df.groupby('uuid'):
    grp = grp.sort_values('signal_time').reset_index(drop=True)
    for i in range(1, len(grp)):
        prev, curr = grp.loc[i-1], grp.loc[i]
        # 3.1) фильтр по прямому разрыву
        d = geodesic((prev['lat'],prev['lon']), (curr['lat'],curr['lon'])).meters
        if d > MAX_SEGMENT_DISTANCE_M:
            continue
        # 3.2) цвет по скорости
        color = speed_color_kmh(curr['speed'])
        if color not in ('yellow','red'):
            continue
        # 3.3) находим ближайшие узлы графа
        n1 = nearest_graph_node(prev['lat'], prev['lon'])
        n2 = nearest_graph_node(curr['lat'], curr['lon'])
        try:
            path = nx.shortest_path(G_roads, source=n1, target=n2, weight='weight')
        except nx.NetworkXNoPath:
            continue
        # 3.4) извлекаем координаты маршрута
        path_coords = [(lon, lat) for lon, lat in path]
        
        # пропускаем «путь» из одной точки
        if len(path_coords) < 2:
            continue
        # 3.5) добавляем в GeoJSON
        features.append({
            "type": "Feature",
            "properties": {
                "uuid": uid,
                "start_time": prev['signal_time'].isoformat(),
                "end_time":   curr['signal_time'].isoformat(),
                "speed_kmh":  round(curr['speed']*3.6,2),
                "color":      color
            },
            "geometry": mapping(LineString(path_coords))
        })

geojson = {"type":"FeatureCollection", "features": features}
with open(OUTPUT_GEOJSON, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"GeoJSON с сегментами на дорогах сохранён в «{OUTPUT_GEOJSON}»")
