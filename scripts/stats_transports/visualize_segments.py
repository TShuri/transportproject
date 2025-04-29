import folium
import json

# Пути к файлам
GEOJSON_PATH = 'segments_yellow_red_on_roads.geojson'
SPEED_STATS_PATH = 'route_uuid_avg_speeds.json'
OUTPUT_HTML = 'segments_speed_groups_map.html'

# Загружаем максимальную скорость из JSON
with open(SPEED_STATS_PATH, 'r', encoding='utf-8') as f:
    speed_data = json.load(f)
max_speed = speed_data['max_speed_kmh']

# Вычисляем границы диапазонов
yellow_upper = max_speed / 2
yellow_lower = yellow_upper / 2
print(f"Диапазоны: красный = 0–{yellow_lower:.2f}, жёлтый = {yellow_lower:.2f}–{yellow_upper:.2f} км/ч")

# Загружаем GeoJSON
with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Центр карты
lats = []
lons = []
for feature in geojson_data['features']:
    coords = feature['geometry']['coordinates']
    for lon, lat in coords:
        lats.append(lat)
        lons.append(lon)
center = [sum(lats) / len(lats), sum(lons) / len(lons)]

# Создаём карту
m = folium.Map(location=center, zoom_start=12, tiles='OpenStreetMap')

# Группы по скорости
speed_red = folium.FeatureGroup(name=f'0–{yellow_lower:.1f} км/ч (красный)', show=True)
speed_yellow = folium.FeatureGroup(name=f'{yellow_lower:.1f}–{yellow_upper:.1f} км/ч (жёлтый)', show=True)

# Добавляем сегменты
for feature in geojson_data['features']:
    if feature['geometry']['type'] != 'LineString':
        continue

    coords = feature['geometry']['coordinates']
    path = [(lat, lon) for lon, lat in coords]
    speed = feature['properties'].get('speed_kmh', 0)

    if speed < yellow_lower:
        color = 'red'
        layer = speed_red
    elif speed < yellow_upper:
        color = 'yellow'
        layer = speed_yellow
    else:
        continue

    folium.PolyLine(
        locations=path,
        color=color,
        weight=5,
        opacity=0.8,
        popup=folium.Popup(f"Скорость: {speed:.1f} км/ч", parse_html=True)
    ).add_to(layer)

# Добавляем группы
speed_red.add_to(m)
speed_yellow.add_to(m)

# Легенда
legend_html = f'''
<div style="
    position: fixed; 
    bottom: 50px; 
    left: 50px; 
    width: 240px;
    background-color: white;
    border: 2px solid grey;
    z-index: 9999;
    font-size: 14px;
    padding: 10px;
">
    <b>Скоростные диапазоны</b><br>
    <i style="background:red; width:15px; height:15px; display:inline-block;"></i> 0–{yellow_lower:.1f} км/ч<br>
    <i style="background:yellow; width:15px; height:15px; display:inline-block;"></i> {yellow_lower:.1f}–{yellow_upper:.1f} км/ч
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Панель слоёв
folium.LayerControl(collapsed=False).add_to(m)

# Сохраняем карту
m.save(OUTPUT_HTML)
print(f"Карта сохранена в {OUTPUT_HTML}")
