import folium
import webbrowser
import json
import geopandas as gpd


def display_geojson_segments(geojson_path, uds_geojson_path):
    """
    Отображает сегменты треков из GeoJSON файла с возможностью наложения и отключения графа УДС
    """
    # Загрузка GeoJSON данных треков
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        if not geojson_data.get('features'):
            print("В GeoJSON файле треков нет данных для отображения")
            return
    except Exception as e:
        print(f"Ошибка загрузки файла треков: {str(e)}")
        return

    # Определяем границы всех сегментов
    all_coords = []
    for feature in geojson_data['features']:
        if feature['geometry']['type'] == 'LineString':
            all_coords.extend(feature['geometry']['coordinates'])

    if not all_coords:
        print("Нет координат для отображения")
        return

    # Автоматическое определение центра карты
    lats = [coord[1] for coord in all_coords]
    lons = [coord[0] for coord in all_coords]
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    # 1. Создаем карту БЕЗ автоматической подложки
    m = folium.Map(location=center, zoom_start=13, tiles=None, control_scale=True)

    # 2. Добавляем OpenStreetMap как отдельный переключаемый слой
    tile_layer = folium.TileLayer(
        tiles='OpenStreetMap',
        name='Базовая карта',
        overlay=True,  # Это ключевой параметр!
        control=True,
        show=True
    ).add_to(m)

    # 3. Добавляем граф УДС
    roads = gpd.read_file(uds_geojson_path).to_crs(epsg=4326)
    folium.GeoJson(
        roads,
        name='Улично-дорожная сеть',
        style_function=lambda feat: {
            "color": "blue",
            "weight": 1,
            "opacity": 0.6
        },
        overlay=True,
        control=True,
        show=False
    ).add_to(m)

    # Создаем группы слоев для треков
    speed_under_5 = folium.FeatureGroup(name='< 5 км/ч', show=True)
    speed_5_to_10 = folium.FeatureGroup(name='5-10 км/ч', show=True)
    speed_10_to_20 = folium.FeatureGroup(name='10-20 км/ч', show=True)

    # Добавляем сегменты в соответствующие группы
    for feature in geojson_data['features']:
        if feature['geometry']['type'] == 'LineString':
            speed = feature['properties'].get('speed_kph', 0)

            if speed < 5:
                color = 'red'
                layer = speed_under_5
            elif speed < 10:
                color = 'orange'
                layer = speed_5_to_10
            elif speed < 20:
                color = 'green'
                layer = speed_10_to_20
            else:
                continue

            folium.PolyLine(
                locations=[(lat, lon) for lon, lat in feature['geometry']['coordinates']],
                color=color,
                weight=5,
                opacity=0.8,
                popup=f"Скорость: {speed:.1f} км/ч"
            ).add_to(layer)

    # Добавляем группы треков на карту
    speed_under_5.add_to(m)
    speed_5_to_10.add_to(m)
    speed_10_to_20.add_to(m)

    # Добавляем легенду
    legend_html = '''
    <div style="
        position: fixed; 
        bottom: 50px; 
        left: 50px; 
        width: 200px;
        background-color: white;
        border: 2px solid grey;
        z-index: 9999;
        font-size: 14px;
        padding: 10px;
    ">
        <b>Скоростные диапазоны</b><br>
        <i style="background:red; width:15px; height:15px; display:inline-block;"></i> < 5 км/ч<br>
        <i style="background:orange; width:15px; height:15px; display:inline-block;"></i> 5-10 км/ч<br>
        <i style="background:green; width:15px; height:15px; display:inline-block;"></i> 10-20 км/ч
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Добавляем расширенный контроль слоев
    folium.LayerControl(collapsed=False).add_to(m)

    # Сохраняем и открываем карту
    output_file = 'speed_segments_with_uds_map.html'
    m.save(output_file)
    webbrowser.open(output_file)
    print(f"Карта сохранена в {output_file}")


# Пример использования
if __name__ == "__main__":
    # Укажите пути к файлам
    geojson_file = "../../sources/stats_ankets/low_speed_segments.geojson"
    uds_file = "../../sources/UDS/Граф Иркутск_link_geojson.geojson"

    # Вызов функции с наложением графа УДС
    display_geojson_segments(geojson_file, uds_file)