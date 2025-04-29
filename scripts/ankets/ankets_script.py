import gpxpy
import folium
import webbrowser
from geopy.distance import distance
from datetime import timedelta
import numpy as np

# === Чтение GPX файла ===
path_anket = '../../sources/geotracks_ankets/Боровский/1_16-К_8.04_вт_6_53_Боровский.gpx'
with open(path_anket, encoding='utf-8') as gpx_file:
    gpx = gpxpy.parse(gpx_file)

# Собираем все точки трека с дополнительной информацией
points = []
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            points.append({
                'latitude': point.latitude,
                'longitude': point.longitude,
                'time': point.time,
                'elevation': point.elevation
            })

# === Расчет статистики ===
total_distance = 0.0
total_time = timedelta()
speeds = []
segments = []

# Рассчитываем параметры для каждого сегмента
for i in range(1, len(points)):
    prev = points[i - 1]
    curr = points[i]

    dist = distance(
        (prev['latitude'], prev['longitude']),
        (curr['latitude'], curr['longitude'])
    ).meters

    time_diff = curr['time'] - prev['time']

    if time_diff.total_seconds() > 0:
        speed = (dist / time_diff.total_seconds()) * 3.6  # км/ч
        total_distance += dist
        total_time += time_diff
        speeds.append(speed)

        # Сохраняем информацию о сегменте
        segments.append({
            'start': (prev['latitude'], prev['longitude']),
            'end': (curr['latitude'], curr['longitude']),
            'speed': speed,
            'distance': dist,
            'time': time_diff
        })

# Расчет средней скорости
avg_speed = (total_distance / total_time.total_seconds()) * 3.6 if total_time.total_seconds() > 0 else 0

# Определение порога для "низкой скорости" (например, 50% от средней)
low_speed_threshold = avg_speed * 0.5

# === Создание карты ===
if points:
    start_coords = (points[0]['latitude'], points[0]['longitude'])
    mymap = folium.Map(location=start_coords, zoom_start=15)

    # Группы слоев
    points_group = folium.FeatureGroup(name='Точки', show=True)
    line_group = folium.FeatureGroup(name='Основной трек', show=True)
    low_speed_group = folium.FeatureGroup(name='Участки с низкой скоростью', show=True)

    # Добавляем точки
    for point in points:
        folium.CircleMarker(
            location=(point['latitude'], point['longitude']),
            radius=3,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.8
        ).add_to(points_group)

    # Добавляем основной трек
    folium.PolyLine(
        locations=[(p['latitude'], p['longitude']) for p in points],
        color='blue',
        weight=3,
        opacity=0.7,
        popup=f"Средняя скорость: {avg_speed:.1f} км/ч"
    ).add_to(line_group)

    # Добавляем участки с низкой скоростью
    for seg in segments:
        if seg['speed'] < low_speed_threshold:
            folium.PolyLine(
                locations=[seg['start'], seg['end']],
                color='red',
                weight=5,
                opacity=0.9,
                popup=f"Низкая скорость: {seg['speed']:.1f} км/ч"
            ).add_to(low_speed_group)

    # Маркеры старта и финиша
    folium.Marker(
        location=(points[0]['latitude'], points[0]['longitude']),
        popup="Старт",
        icon=folium.Icon(color='green')
    ).add_to(mymap)

    folium.Marker(
        location=(points[-1]['latitude'], points[-1]['longitude']),
        popup="Финиш",
        icon=folium.Icon(color='red')
    ).add_to(mymap)

    # Добавляем группы на карту
    points_group.add_to(mymap)
    line_group.add_to(mymap)
    low_speed_group.add_to(mymap)

    # Переключатель слоев
    folium.LayerControl().add_to(mymap)

    # Кастомная легенда
    legend_html = f'''
    <div style="
        position: fixed; 
        bottom: 50px; 
        left: 50px; 
        width: 250px;
        height: 160px;
        background-color: white;
        border: 2px solid grey;
        z-index: 9999;
        font-size: 14px;
        padding: 10px;
    ">
        <b>Статистика маршрута</b><br>
        Средняя скорость: {avg_speed:.1f} км/ч<br>
        Порог низкой скорости: {low_speed_threshold:.1f} км/ч<br>
        Общее расстояние: {total_distance / 1000:.2f} км<br>
        Общее время: {str(total_time)[:-7]}<br>
        Точек: {len(points)}<br>
        <i style="background:red; width:15px; height:15px; display:inline-block;"></i> Участки с низкой скоростью
    </div>
    '''
    mymap.get_root().html.add_child(folium.Element(legend_html))

    # Сохраняем карту
    mymap.save('track_with_low_speed.html')
    webbrowser.open('track_with_low_speed.html')
    print(f"Карта сохранена. Средняя скорость: {avg_speed:.1f} км/ч")
else:
    print("Не удалось извлечь точки трека из GPX файла")