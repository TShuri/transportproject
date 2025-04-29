import pandas as pd
import folium
import numpy as np
import webbrowser
import os
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
import zipfile
import csv
import io
import geopandas as gpd
from shapely.strtree import STRtree
from shapely.geometry import Point
from geopy.distance import geodesic
import networkx as nx
from shapely.geometry import LineString
import scipy.spatial

# Загрузка данных из CSV-файла с указанием правильного разделителя
print("Загрузка данных из CSV-файла...")
df = pd.read_csv('../../sources/current_route/current_route.csv', sep=';', low_memory=False)

# Вывод информации о столбцах для отладки
print("Доступные столбцы в файле:")
print(df.columns.tolist())

# Проверка наличия необходимых столбцов для координат и скорости
required_columns = ['lat', 'lon', 'speed', 'signal_time']
for col in required_columns:
    if col not in df.columns:
        print(f"Критическая ошибка: столбец '{col}' отсутствует в файле данных")
        exit(1)

# Удаление строк с отсутствующими координатами
df = df.dropna(subset=['lat', 'lon', 'speed', 'signal_time'])

# Преобразование signal_time в datetime, если это строка
if isinstance(df['signal_time'].iloc[0], str):
    df['signal_time'] = pd.to_datetime(df['signal_time'])

# Сортировка по времени
df = df.sort_values('signal_time')

# Вычисление средней скорости по всему маршруту
avg_speed = df['speed'].mean()
# порог средней и «половинчатой» скоростей
mid_speed = avg_speed / 2

avg_speed_kmh = avg_speed * 3.6
mid_speed_kmh = avg_speed_kmh / 2


def speed_color_kmh(v_mps):
    """
    v_mps — скорость в м/с
    переводим в км/ч и раскрашиваем:
      ≥ avg_speed_kmh → green
      ≥ mid_speed_kmh → orange
      < mid_speed_kmh → red
    """
    v_kmh = v_mps * 3.6
    if v_kmh >= avg_speed_kmh:
        return 'green'
    elif v_kmh >= mid_speed_kmh:
        return 'orange'
    else:
        return 'red'


print(f"Загружено {len(df)} записей с координатами")

# Определение остановок
print("Определение остановок...")

# Параметры для определения остановок
SPEED_THRESHOLD = 1.9  # м/с
MIN_STOP_DURATION = 35  # секунды - изменено с 20 на 45 секунд
DISTANCE_THRESHOLD = 0.001  # примерно 100 метров в градусах
STOP_AGGREGATION_THRESHOLD = 0.0001  # примерно 300 метров для агрегации остановок

# Находим точки с низкой скоростью
low_speed_points = df[df['speed'] < SPEED_THRESHOLD].copy()

if len(low_speed_points) > 0:
    # Вычисляем продолжительность остановки для каждой точки
    low_speed_points['next_time'] = low_speed_points['signal_time'].shift(-1)
    low_speed_points['duration'] = (low_speed_points['next_time'] - low_speed_points['signal_time']).dt.total_seconds()
    low_speed_points = low_speed_points.dropna(subset=['duration'])

    # Фильтруем точки с достаточной продолжительностью остановки
    potential_stops = low_speed_points[low_speed_points['duration'] > MIN_STOP_DURATION]

    if len(potential_stops) > 0:
        # Используем DBSCAN для кластеризации близких точек в остановки
        coords = potential_stops[['lat', 'lon']].values
        clustering = DBSCAN(eps=DISTANCE_THRESHOLD, min_samples=1).fit(coords)

        # Создаем копию DataFrame для избежания предупреждения SettingWithCopyWarning
        potential_stops = potential_stops.copy()
        potential_stops['cluster_id'] = clustering.labels_

        # Группируем точки по кластерам для получения уникальных остановок
        # Используем другое имя для агрегации количества точек
        stops = potential_stops.groupby('cluster_id').agg({
            'lat': 'mean',
            'lon': 'mean',
            'signal_time': 'min',
            'duration': 'sum',
            'cluster_id': 'size'  # Используем 'size' вместо 'count'
        })

        # Переименовываем столбец с количеством точек и сбрасываем индекс
        stops = stops.rename(columns={'cluster_id': 'point_count'}).reset_index()

        # Добавляем идентификаторы остановок
        stops['stop_id'] = 'stop_' + stops.index.astype(str)
        stops['stop_name'] = 'Остановка ' + stops.index.astype(str)

        # Определяем начальную и конечную остановки
        stops['is_first'] = False
        stops['is_last'] = False

        if len(stops) > 0:
            # Находим остановку, ближайшую к началу маршрута
            first_time = df['signal_time'].min()
            stops['time_from_start'] = abs((stops['signal_time'] - first_time).dt.total_seconds())
            first_stop_idx = stops['time_from_start'].idxmin()
            stops.loc[first_stop_idx, 'is_first'] = True
            stops.loc[first_stop_idx, 'stop_name'] = 'Начальная остановка'

            # Находим остановку, ближайшую к концу маршрута
            last_time = df['signal_time'].max()
            stops['time_to_end'] = abs((stops['signal_time'] - last_time).dt.total_seconds())
            last_stop_idx = stops['time_to_end'].idxmin()
            stops.loc[last_stop_idx, 'is_last'] = True
            stops.loc[last_stop_idx, 'stop_name'] = 'Конечная остановка'

            print(f"Найдено {len(stops)} остановок")
        else:
            print("Остановки не найдены")
            stops = pd.DataFrame(
                columns=['stop_id', 'stop_name', 'lat', 'lon', 'is_first', 'is_last', 'point_count', 'duration'])
    else:
        print("Не найдено точек с достаточной продолжительностью остановки")
        stops = pd.DataFrame(
            columns=['stop_id', 'stop_name', 'lat', 'lon', 'is_first', 'is_last', 'point_count', 'duration'])
else:
    print("Не найдено точек с низкой скоростью")
    stops = pd.DataFrame(
        columns=['stop_id', 'stop_name', 'lat', 'lon', 'is_first', 'is_last', 'point_count', 'duration'])

# Создание базовой карты
print("Создание карты...")
# Определение центра карты (средние координаты)
center_lat = df['lat'].mean()
center_lon = df['lon'].mean()
map_tracks = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles=None)
# Добавление отключаемого слоя OpenStreetMap
folium.TileLayer(
    tiles='OpenStreetMap',
    name='OSM карта',
    control=True,
    overlay=True,
    show=True
).add_to(map_tracks)

# — ВСТАВКА: загрузка и отображение графа дорожной сети
roads = gpd.read_file("../../sources/UDS/Граф Иркутск_link.SHP").to_crs(epsg=4326)
# Собираем список геометрий дорог и строим STR-дерево
road_geoms = list(roads.geometry)
road_tree = STRtree(road_geoms)


def snap_to_road_point(lat, lon):
    pt = Point(lon, lat)
    # nearest возвращает индекс ближайшей геометрии
    idx = road_tree.nearest(pt)
    nearest_line = road_geoms[idx]
    # проекция точки на линию
    proj_pt = nearest_line.interpolate(nearest_line.project(pt))
    return proj_pt.y, proj_pt.x  # y=lat, x=lon


print("Снаппим все точки маршрута на сеть дорог…")
# Перезаписываем lat, lon в исходном df — дальше в коде менять ничего не нужно
df[['lat', 'lon']] = df.apply(
    lambda r: pd.Series(snap_to_road_point(r['lat'], r['lon'])),
    axis=1
)

fg_roads = folium.FeatureGroup(name="Сеть дорог", show=False)
folium.GeoJson(
    roads,
    style_function=lambda feat: {
        "color": "blue",
        "weight": 1,
        "opacity": 0.5
    }
).add_to(fg_roads)
fg_roads.add_to(map_tracks)

# Создаем слой для точек маршрута
points_layer = folium.FeatureGroup(name="Точки маршрута")

# Добавление всех точек на карту
print("Добавление точек на карту...")
for idx, row in df.iterrows():
    # Создаем всплывающую подсказку с информацией о точке
    popup_text = f"Точка #{idx}<br>Координаты: {row['lat']}, {row['lon']}<br>Скорость: {row['speed']} м/с"

    # Добавляем дополнительную информацию, если она есть
    if 'signal_time' in df.columns:
        popup_text += f"<br>Время: {row['signal_time']}"
    if 'direction' in df.columns:
        popup_text += f"<br>Направление: {row['direction']}"

    # Определяем цвет точки в зависимости от скорости
    color = 'blue'
    if row['speed'] < SPEED_THRESHOLD:
        color = 'orange'  # Точки с низкой скоростью

    # Добавляем маркер для каждой точки
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=3,  # Маленький размер для точек
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=popup_text,
        tooltip=f"Точка #{idx}"
    ).add_to(points_layer)

# Создаем слой для остановок
stops_layer = folium.FeatureGroup(name="Остановки")

# Добавление остановок на карту
if len(stops) > 0:
    print(f"Найдено {len(stops)} остановок перед агрегацией")

    # Дополнительная агрегация остановок
    if len(stops) > 1:
        print("Выполняем дополнительную агрегацию остановок...")

        # Используем координаты остановок для второго уровня кластеризации
        stop_coords = stops[['lat', 'lon']].values
        stop_clustering = DBSCAN(eps=STOP_AGGREGATION_THRESHOLD, min_samples=1).fit(stop_coords)
        stops['stop_cluster'] = stop_clustering.labels_

        # Агрегируем остановки по кластерам
        aggregated_stops = stops.groupby('stop_cluster').agg({
            'lat': 'mean',
            'lon': 'mean',
            'signal_time': 'min',
            'duration': 'sum',
            'point_count': 'sum',
            'is_first': 'any',
            'is_last': 'any'
        }).reset_index()

        # === ДОПОЛНИТЕЛЬНЫЙ АНАЛИЗ ДЛЯ КОНЕЧНЫХ ОСТАНОВОК ===

        # Вычисляем медиану времени остановки
        median_stop_duration = aggregated_stops['duration'].median()

        # Порог — если остановка в среднем дольше чем X раз медианы
        DURATION_FACTOR = 3.0
        LONG_STOP_THRESHOLD = median_stop_duration * DURATION_FACTOR

        # Помечаем остановки с большим временем ожидания
        aggregated_stops['is_potential_terminal'] = aggregated_stops['duration'] > LONG_STOP_THRESHOLD

        # Исключаем редкие точки (мало точек -> возможен выброс)
        MIN_POINTS = 10
        aggregated_stops.loc[aggregated_stops['point_count'] < MIN_POINTS, 'is_potential_terminal'] = False

        # (опционально) исключаем ближайшие к первой/последней точке, чтобы не дублировать
        aggregated_stops['is_terminal'] = aggregated_stops['is_potential_terminal']
        aggregated_stops.loc[aggregated_stops['is_first'] | aggregated_stops['is_last'], 'is_terminal'] = True

        # Добавляем новые идентификаторы и имена для агрегированных остановок
        aggregated_stops['stop_id'] = 'stop_' + aggregated_stops.index.astype(str)
        aggregated_stops['stop_name'] = 'Остановка ' + aggregated_stops.index.astype(str)

        # Обновляем имена для начальной и конечной остановок
        aggregated_stops.loc[aggregated_stops['is_first'], 'stop_name'] = 'Начальная остановка'
        aggregated_stops.loc[aggregated_stops['is_last'], 'stop_name'] = 'Конечная остановка'

        # Заменяем исходный DataFrame агрегированным
        stops = aggregated_stops

        # Сохраняем связи остановки ↔ uuid
        stops_uuids = potential_stops[['lat', 'lon', 'cluster_id', 'uuid']].copy()

        # Привязываем к кластеру (по координатам)
        stops_uuids['stop_cluster'] = clustering.labels_

        # Считаем количество уникальных транспорта (uuid) на каждой остановке
        uuid_counts = stops_uuids.groupby('stop_cluster')['uuid'].nunique().reset_index()
        uuid_counts.columns = ['stop_cluster', 'unique_uuids']

        # Объединяем с aggregated_stops
        aggregated_stops = aggregated_stops.merge(uuid_counts, on='stop_cluster', how='left')

        # Фильтруем — только остановки, которые посещают >= MIN_UUIDS транспорта
        MIN_UUIDS = 3
        aggregated_stops['is_potential_terminal'] = (
                (aggregated_stops['duration'] > median_stop_duration * DURATION_FACTOR) &
                (aggregated_stops['point_count'] >= MIN_POINTS) &
                (aggregated_stops['unique_uuids'] >= MIN_UUIDS)
        )

        print(f"После агрегации осталось {len(stops)} остановок")

    print("Добавление остановок на карту...")
    for idx, stop in stops.iterrows():
        # Определяем цвет и иконку в зависимости от типа остановки
        if stop['is_first']:
            icon_color = 'green'
            icon_name = 'play'
            stop_type = 'Начальная остановка'
        elif stop['is_last']:
            icon_color = 'red'
            icon_name = 'stop'
            stop_type = 'Финальная по времени'
        elif 'is_terminal' in stop and stop['is_terminal']:
            icon_color = 'darkred'
            icon_name = 'flag-checkered'
            stop_type = 'Конечная остановка'
            if 'unique_uuids' in stop:
                popup_text += f"<br>UUID транспорта: {stop['unique_uuids']}"
        else:
            icon_color = 'blue'
            icon_name = 'bus'
            stop_type = 'Промежуточная остановка'

        # Форматируем время остановки в минуты и секунды
        stop_minutes = int(stop['duration'] // 60)
        stop_seconds = int(stop['duration'] % 60)
        stop_time_str = f"{stop_minutes} мин {stop_seconds} сек"

        # Создаем всплывающую подсказку с информацией об остановке
        popup_text = f"{stop_type}<br>ID: {stop['stop_id']}<br>Название: {stop['stop_name']}<br>Координаты: {stop['lat']}, {stop['lon']}"
        popup_text += f"<br>Количество точек: {stop['point_count']}<br>Время остановки: {stop_time_str}"

        # Добавляем маркер для остановки
        folium.Marker(
            location=[stop['lat'], stop['lon']],
            popup=popup_text,
            tooltip=f"{stop['stop_name']} ({stop['point_count']} точек, {stop_time_str})",
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix='fa')
        ).add_to(stops_layer)

# Добавляем слои на карту
points_layer.add_to(map_tracks)
stops_layer.add_to(map_tracks)


def build_graph_from_roads(roads_gdf):
    G = nx.Graph()
    for i, row in roads_gdf.iterrows():
        geom = row.geometry
        if isinstance(geom, LineString):
            coords = list(geom.coords)
            for start, end in zip(coords[:-1], coords[1:]):
                dist = Point(start).distance(Point(end))
                G.add_edge(start, end, weight=dist, geometry=LineString([start, end]))
    return G


print("Создаём граф дорог…")
G_roads = build_graph_from_roads(roads)

nodes = list(G_roads.nodes)
# узлы хранятся как (x, y) == (lon, lat)
nodes_coords = [(x, y) for x, y in nodes]
kdtree = scipy.spatial.KDTree(nodes_coords)


# 2) Быстрый nearest_graph_node через KDTree
def nearest_graph_node(point, G, kdtree=kdtree, nodes=nodes):
    lat, lon = point
    # query принимает (lon, lat)
    _, idx = kdtree.query((lon, lat))
    return nodes[idx]


print("Добавление маршрутов по uuid...")

uuid_layers = {}

for uid in df['uuid'].unique():
    sub_df = df[df['uuid'] == uid].sort_values('signal_time')
    uid_layer = folium.FeatureGroup(name=f"Id Транспорта {uid}", show=False)

    prev_point = None
    for _, row in sub_df.iterrows():
        current_point = (row['lat'], row['lon'])

        if prev_point:
            start_node = nearest_graph_node(prev_point, G_roads)
            end_node = nearest_graph_node(current_point, G_roads)

            try:
                # Ищем кратчайший путь между точками
                path_nodes = nx.shortest_path(G_roads, source=start_node, target=end_node, weight='weight')
                path_coords = [(y, x) for x, y in path_nodes]  # переворачиваем в (lat, lon)

                # Получаем скорость этого сегмента:
                seg_speed_mps = row['speed']
                seg_speed_kmh = seg_speed_mps * 3.6

                folium.PolyLine(
                    path_coords,
                    color=speed_color_kmh(seg_speed_mps),
                    weight=3,
                    opacity=0.8,
                    tooltip=(
                        f"UUID: {uid}<br>"
                        f"Время: {row['signal_time']}<br>"
                        f"Скорость: {seg_speed_kmh:.1f} км/ч<br>"
                        f"Средняя: {avg_speed_kmh:.1f} км/ч"
                    )
                ).add_to(uid_layer)
            except nx.NetworkXNoPath:
                print(f"⚠️ Нет пути между точками для UUID {uid}")

        prev_point = current_point

    uuid_layers[uid] = uid_layer
    uid_layer.add_to(map_tracks)

# Добавление всех слоёв
points_layer.add_to(map_tracks)
stops_layer.add_to(map_tracks)
for uid_layer in uuid_layers.values():
    uid_layer.add_to(map_tracks)

# Панель управления слоями
folium.LayerControl(collapsed=False).add_to(map_tracks)

# Сохранение карты в HTML-файл
output_file = 'transport_tracks_with_stops.html'
# Добавление легенды со средней скоростью
legend_html = f"""
<div style="position: fixed; bottom: 50px; left: 50px; width: 200px; 
     background-color: white; border:2px solid grey; z-index:9999; padding: 10px; font-size:14px;">
  <b>Легенда скорости</b><br>
  <div style="display: flex; align-items: center; margin-top:4px;">
    <div style="width:16px; height:16px; background:green; margin-right:6px;"></div>
    ≥ {avg_speed_kmh:.1f} км/ч
  </div>
  <div style="display: flex; align-items: center; margin-top:4px;">
    <div style="width:16px; height:16px; background:orange; margin-right:6px;"></div>
    {mid_speed_kmh:.1f} – {avg_speed_kmh:.1f} км/ч
  </div>
  <div style="display: flex; align-items: center; margin-top:4px;">
    <div style="width:16px; height:16px; background:red; margin-right:6px;"></div>
    < {mid_speed_kmh:.1f} км/ч
  </div>
</div>
"""

map_tracks.get_root().html.add_child(folium.Element(legend_html))
map_tracks.save(output_file)
print(f"Карта сохранена в файл: {output_file}")

# Экспорт в формат GTFS
print("Экспорт данных в формат GTFS...")

# Создаем временную директорию для файлов GTFS
gtfs_dir = 'gtfs_temp'
os.makedirs(gtfs_dir, exist_ok=True)

# Создаем файл stops.txt с дополнительной информацией
stops_file = os.path.join(gtfs_dir, 'stops.txt')
if len(stops) > 0:
    # Добавляем дополнительные столбцы для экспорта
    stops_export = stops[['stop_id', 'stop_name', 'lat', 'lon']].copy()
    # Добавляем информацию о количестве точек и времени остановки в описание
    stops_export['stop_desc'] = stops.apply(
        lambda x: f"Точек: {x['point_count']}, Время: {int(x['duration'] // 60)} мин {int(x['duration'] % 60)} сек",
        axis=1
    )
    stops_export.to_csv(stops_file, index=False)
else:
    # Создаем пустой файл с заголовками
    with open(stops_file, 'w') as f:
        f.write('stop_id,stop_name,lat,lon,stop_desc\n')

# Создаем файл routes.txt
routes_file = os.path.join(gtfs_dir, 'routes.txt')
with open(routes_file, 'w') as f:
    f.write('route_id,route_short_name,route_long_name,route_type\n')
    f.write('route_1,1,Маршрут 1,3\n')  # 3 - транспорт

# Создаем файл trips.txt
trips_file = os.path.join(gtfs_dir, 'trips.txt')
with open(trips_file, 'w') as f:
    f.write('route_id,service_id,trip_id,trip_headsign\n')
    f.write('route_1,weekday,trip_1,Маршрут 1\n')

# Создаем файл calendar.txt
calendar_file = os.path.join(gtfs_dir, 'calendar.txt')
with open(calendar_file, 'w') as f:
    f.write('service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n')
    f.write('weekday,1,1,1,1,1,0,0,20230101,20231231\n')

# Создаем файл stop_times.txt
stop_times_file = os.path.join(gtfs_dir, 'stop_times.txt')
if len(stops) > 0:
    with open(stop_times_file, 'w') as f:
        f.write('trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign\n')

        # Сортируем остановки по времени
        sorted_stops = stops.sort_values('signal_time')

        # Получаем время первой остановки
        first_time = sorted_stops['signal_time'].iloc[0]

        # Добавляем каждую остановку
        for i, (idx, stop) in enumerate(sorted_stops.iterrows()):
            # Вычисляем время прибытия и отправления
            time_diff = (stop['signal_time'] - first_time).total_seconds()
            hours = int(time_diff // 3600)
            minutes = int((time_diff % 3600) // 60)
            seconds = int(time_diff % 60)

            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Форматируем информацию о количестве точек и времени остановки
            stop_info = f"Точек: {stop['point_count']}, Время: {int(stop['duration'] // 60)} мин {int(stop['duration'] % 60)} сек"

            # Добавляем запись в файл
            f.write(f'trip_1,{time_str},{time_str},{stop["stop_id"]},{i + 1},{stop_info}\n')
else:
    # Создаем пустой файл с заголовками
    with open(stop_times_file, 'w') as f:
        f.write('trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign\n')

# Создаем файл agency.txt
agency_file = os.path.join(gtfs_dir, 'agency.txt')
with open(agency_file, 'w') as f:
    f.write('agency_id,agency_name,agency_url,agency_timezone\n')
    f.write('1,Транспортная компания,http://example.com,Europe/Moscow\n')

# Создаем ZIP-архив с файлами GTFS
gtfs_zip = 'transport_gtfs.zip'
with zipfile.ZipFile(gtfs_zip, 'w') as zipf:
    for root, dirs, files in os.walk(gtfs_dir):
        for file in files:
            zipf.write(os.path.join(root, file), arcname=file)

print(f"Данные экспортированы в формат GTFS: {gtfs_zip}")

# Автоматическое открытие карты в браузере
html_path = os.path.abspath(output_file)
file_url = f'file://{html_path}'
print(f"Открываю карту в браузере: {file_url}")
webbrowser.open(file_url)

print("Готово!")