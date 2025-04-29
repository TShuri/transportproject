import gpxpy
import folium
import webbrowser
import argparse
from geopy.distance import distance
from datetime import timedelta

def parse_gpx_file(gpx_path):
    """Парсинг GPX файла и извлечение точек трека"""
    with open(gpx_path, encoding='utf-8') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

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
    return points

def calculate_statistics(points):
    """Расчет статистики по точкам трека"""
    total_distance = 0.0
    total_time = timedelta()
    speeds = []
    segments = []

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

            segments.append({
                'start': (prev['latitude'], prev['longitude']),
                'end': (curr['latitude'], curr['longitude']),
                'speed': speed,
                'distance': dist,
                'time': time_diff
            })

    avg_speed = (total_distance / total_time.total_seconds()) * 3.6 if total_time.total_seconds() > 0 else 0
    low_speed_threshold = avg_speed * 0.5

    return {
        'total_distance': total_distance,
        'total_time': total_time,
        'avg_speed': avg_speed,
        'low_speed_threshold': low_speed_threshold,
        'segments': segments
    }

def create_map(points, stats):
    """Создание интерактивной карты с треком"""
    start_coords = (points[0]['latitude'], points[0]['longitude'])
    mymap = folium.Map(location=start_coords, zoom_start=15)

    # Группы слоев
    points_group = folium.FeatureGroup(name='Точки', show=False)
    line_group = folium.FeatureGroup(name='Основной трек', show=True)
    low_speed_group = folium.FeatureGroup(name='Участки с низкой скоростью', show=True)

    # Основной трек
    folium.PolyLine(
        locations=[(p['latitude'], p['longitude']) for p in points],
        color='blue',
        weight=3,
        opacity=0.7,
        popup=f"Средняя скорость: {stats['avg_speed']:.1f} км/ч"
    ).add_to(line_group)

    # Участки с низкой скоростью
    for seg in stats['segments']:
        if seg['speed'] < stats['low_speed_threshold']:
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

    # Добавление групп на карту
    points_group.add_to(mymap)
    line_group.add_to(mymap)
    low_speed_group.add_to(mymap)

    # Управление слоями
    folium.LayerControl().add_to(mymap)

    # Легенда
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
        Средняя скорость: {stats['avg_speed']:.1f} км/ч<br>
        Порог низкой скорости: {stats['low_speed_threshold']:.1f} км/ч<br>
        Общее расстояние: {stats['total_distance'] / 1000:.2f} км<br>
        Общее время: {str(stats['total_time'])[:-7]}<br>
        Точек: {len(points)}<br>
        <i style="background:red; width:15px; height:15px; display:inline-block;"></i> Участки с низкой скоростью
    </div>
    '''
    mymap.get_root().html.add_child(folium.Element(legend_html))

    return mymap

def main(gpx_path):
    """Основная функция обработки GPX файла"""
    try:
        points = parse_gpx_file(gpx_path)
        if not points:
            print("Не удалось извлечь точки трека из GPX файла")
            return

        stats = calculate_statistics(points)
        print(f"Обработка GPX файла: {gpx_path}")
        print(f"Средняя скорость: {stats['avg_speed']:.1f} км/ч")

        mymap = create_map(points, stats)
        output_file = gpx_path.replace('.gpx', '_map.html')
        mymap.save(output_file)
        webbrowser.open(output_file)
        print(f"Карта сохранена в {output_file}")

    except Exception as e:
        print(f"Ошибка при обработке файла: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Анализ GPX треков')
    parser.add_argument('--gpx_file', type=str, help='Путь к GPX файлу')
    args = parser.parse_args()

    main(args.gpx_file)