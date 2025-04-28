import gpxpy
import geopy.distance
import matplotlib.pyplot as plt
import pandas as pd
import folium
import webbrowser
from folium.plugins import MarkerCluster

# === Чтение GPX файла ===
path_anket = '../../sources/geotracks_ankets/Боровский/1_16-К_8.04_вт_6_53_Боровский.gpx'
with open(path_anket, encoding='utf-8') as gpx_file:
    gpx = gpxpy.parse(gpx_file)

points = []
total_distance = 0.0
max_speed = 0.0

# Извлечение данных
for track in gpx.tracks:
    for segment in track.segments:
        last_point = None
        last_time = None
        for point in segment.points:
            points.append({
                'latitude': point.latitude,
                'longitude': point.longitude,
                'elevation': point.elevation,
                'time': point.time
            })
            if last_point and last_time:
                dist = geopy.distance.distance(
                    (last_point.latitude, last_point.longitude),
                    (point.latitude, point.longitude)
                ).meters
                time_delta = (point.time - last_time).total_seconds()

                if time_delta > 0:
                    speed = dist / time_delta
                    if speed > max_speed:
                        max_speed = speed

                total_distance += dist

            last_point = point
            last_time = point.time

# === Создание DataFrame ===
df = pd.DataFrame(points)
df['time_diff'] = df['time'].diff().dt.total_seconds()

distances = []
speeds = []
for i in range(1, len(df)):
    prev = (df.iloc[i-1]['latitude'], df.iloc[i-1]['longitude'])
    curr = (df.iloc[i]['latitude'], df.iloc[i]['longitude'])
    dist = geopy.distance.distance(prev, curr).meters
    time_delta = (df.iloc[i]['time'] - df.iloc[i-1]['time']).total_seconds()

    if time_delta > 0:
        speed_m_s = dist / time_delta
        speed_kph = speed_m_s * 3.6
    else:
        speed_kph = 0

    distances.append(dist)
    speeds.append(speed_kph)

distances = [0] + distances
speeds = [0] + speeds

df['distance'] = distances
df['speed'] = speeds
df['cumulative_distance'] = df['distance'].cumsum()

# === Создание карты ===
start_coords = (df.iloc[0]['latitude'], df.iloc[0]['longitude'])
mymap = folium.Map(location=start_coords, zoom_start=15)

# Группы слоев
points_group = folium.FeatureGroup(name='Геометки')
track_group = folium.FeatureGroup(name='Маршрут')

# Добавляем все точки в отдельную группу
for idx, row in df.iterrows():
    color = 'red' if row['speed'] < 5 else 'blue'
    folium.CircleMarker(
        location=(row['latitude'], row['longitude']),
        radius=3,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=f"Скорость: {row['speed']:.1f} км/ч\nВысота: {row['elevation']} м\nВремя: {row['time']}"
    ).add_to(points_group)

# Функция выбора цвета по скорости
def get_color_by_speed(speed):
    if 0 <= speed <= 10:
        return 'gray'
    elif 11 <= speed <= 20:
        return 'lightblue'
    elif 21 <= speed <= 30:
        return 'blue'
    elif 31 <= speed <= 40:
        return 'lightgreen'
    else:  # >40
        return 'green'

# Добавляем отрезки маршрута в отдельную группу + подписи скоростей
for i in range(1, len(df)):
    prev_point = df.iloc[i-1]
    curr_point = df.iloc[i]
    segment = [
        (prev_point['latitude'], prev_point['longitude']),
        (curr_point['latitude'], curr_point['longitude'])
    ]
    color = get_color_by_speed(curr_point['speed'])

    folium.PolyLine(
        locations=segment,
        color=color,
        weight=4,
        opacity=0.8
    ).add_to(track_group)

    # Подпись скорости в центре отрезка
    mid_lat = (prev_point['latitude'] + curr_point['latitude']) / 2
    mid_lon = (prev_point['longitude'] + curr_point['longitude']) / 2
    folium.map.Marker(
        [mid_lat, mid_lon],
        icon=folium.DivIcon(
            html=f"""<div style="font-size: 8pt; color : black">{curr_point['speed']:.1f} км/ч</div>"""
        )
    ).add_to(track_group)

# Добавляем маркеры старта и финиша
folium.Marker(
    location=(df.iloc[0]['latitude'], df.iloc[0]['longitude']),
    popup="Старт",
    icon=folium.Icon(color='green')
).add_to(mymap)

folium.Marker(
    location=(df.iloc[-1]['latitude'], df.iloc[-1]['longitude']),
    popup="Финиш",
    icon=folium.Icon(color='red')
).add_to(mymap)

# Добавляем группы на карту
points_group.add_to(mymap)
track_group.add_to(mymap)

# Добавляем переключатель слоев
folium.LayerControl().add_to(mymap)

# === Добавляем легенду ===
legend_html = '''
<div style="
position: fixed;
bottom: 50px; left: 50px; width: 180px; height: 160px;
background-color: white;
border:2px solid grey; z-index:9999; font-size:14px;
padding: 10px;
">
<b>Скорость (км/ч)</b><br>
<i style="background:gray;color:white;">&nbsp;&nbsp;0-10&nbsp;&nbsp;</i> Серый<br>
<i style="background:lightblue;">&nbsp;&nbsp;11-20&nbsp;&nbsp;</i> Голубой<br>
<i style="background:blue;color:white;">&nbsp;&nbsp;21-30&nbsp;&nbsp;</i> Синий<br>
<i style="background:lightgreen;">&nbsp;&nbsp;31-40&nbsp;&nbsp;</i> Светло-зелёный<br>
<i style="background:green;color:white;">&nbsp;&nbsp;>40&nbsp;&nbsp;</i> Тёмно-зелёный
</div>
'''
mymap.get_root().html.add_child(folium.Element(legend_html))

# Сохраняем карту
mymap.save('map_ankets.html')

webbrowser.open('map_ankets.html')
print("Карта сохранена в файл 'map_ankets.html'. Откройте его в браузере!")
