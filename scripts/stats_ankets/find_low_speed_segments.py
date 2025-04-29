import gpxpy
from geopy.distance import distance
from datetime import timedelta
import json
import sys
import os
from collections import defaultdict


def analyze_and_append_low_speed_segments(gpx_path, output_geojson_path):
    """
    Анализирует GPX файл и добавляет участки с низкой скоростью в GeoJSON

    Параметры:
        gpx_path (str): Путь к GPX файлу
        output_geojson_path (str): Путь к GeoJSON файлу для сохранения (будет создан или дополнен)

    Возвращает:
        dict: Результаты анализа
    """
    # Чтение GPX файла
    with open(gpx_path, encoding='utf-8') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Собираем все точки трека
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

    # Расчет статистики
    total_distance = 0.0
    total_time = timedelta()
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

            segments.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [
                        [prev['longitude'], prev['latitude']],
                        [curr['longitude'], curr['latitude']]
                    ]
                },
                'properties': {
                    'speed_kph': speed,
                    'distance_m': dist,
                    'time_sec': time_diff.total_seconds(),
                    'start_time': prev['time'].isoformat(),
                    'end_time': curr['time'].isoformat(),
                    'source_file': os.path.basename(gpx_path)
                }
            })

    # Расчет средней скорости
    avg_speed = (total_distance / total_time.total_seconds()) * 3.6 if total_time.total_seconds() > 0 else 0

    # Определение порога для "низкой скорости" (50% от средней)
    low_speed_threshold = avg_speed * 0.5

    # Фильтрация сегментов с низкой скоростью
    low_speed_features = [seg for seg in segments if seg['properties']['speed_kph'] < low_speed_threshold]

    # Загрузка существующего GeoJSON или создание нового
    if os.path.exists(output_geojson_path):
        with open(output_geojson_path, 'r', encoding='utf-8') as f:
            geojson = json.load(f)

        # Инициализация отсутствующих полей
        if 'properties' not in geojson:
            geojson['properties'] = {}
        if 'sources_processed' not in geojson['properties']:
            geojson['properties']['sources_processed'] = []
        if 'total_distance_m' not in geojson['properties']:
            geojson['properties']['total_distance_m'] = 0
        if 'total_time_sec' not in geojson['properties']:
            geojson['properties']['total_time_sec'] = 0
    else:
        geojson = {
            'type': 'FeatureCollection',
            'features': [],
            'properties': {
                'sources_processed': [],
                'total_distance_m': 0,
                'total_time_sec': 0,
                'last_avg_speed_kph': None,
                'last_low_speed_threshold_kph': None
            }
        }

    # Добавление новых данных
    geojson['features'].extend(low_speed_features)
    geojson['properties']['sources_processed'].append(os.path.basename(gpx_path))
    geojson['properties']['total_distance_m'] += total_distance
    geojson['properties']['total_time_sec'] += total_time.total_seconds()
    geojson['properties']['last_avg_speed_kph'] = avg_speed
    geojson['properties']['last_low_speed_threshold_kph'] = low_speed_threshold

    # Сохранение обновленного файла
    with open(output_geojson_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    return {
        'avg_speed': avg_speed,
        'low_speed_threshold': low_speed_threshold,
        'low_speed_segments_count': len(low_speed_features),
        'output_file': output_geojson_path,
        'total_features': len(geojson['features'])
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python script.py <gpx_file> <output_geojson>")
        sys.exit(1)

    gpx_path = sys.argv[1]
    output_path = sys.argv[2]

    result = analyze_and_append_low_speed_segments(gpx_path, output_path)

    print("=== Результаты анализа ===")
    print(f"Обработан файл: {gpx_path}")
    print(f"Средняя скорость: {result['avg_speed']:.1f} км/ч")
    print(f"Порог низкой скорости: {result['low_speed_threshold']:.1f} км/ч")
    print(f"Добавлено участков с низкой скоростью: {result['low_speed_segments_count']}")
    print(f"Всего участков в GeoJSON: {result['total_features']}")
    print(f"GeoJSON файл обновлен: {result['output_file']}")