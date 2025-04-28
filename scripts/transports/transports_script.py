import pandas as pd
import geopandas as gpd
import folium
import random
import webbrowser
from shapely.ops import nearest_points
from xlsx2csv import Xlsx2csv

# 1) Excel → CSV
# track_file = "bus10full.xlsx"
# Xlsx2csv(track_file, outputencoding="utf-8").convert("tracks.csv")

# 2) Читаем и чистим
tracks = pd.read_csv('../../sources/other/route10.csv', sep=';', low_memory=False)
tracks['lat'] = pd.to_numeric(tracks['lat'], errors='coerce')
tracks['lon'] = pd.to_numeric(tracks['lon'], errors='coerce')
tracks = tracks.dropna(subset=['lat', 'lon', 'uuid']).reset_index(drop=True)

# 3) Дорожная сеть
UDS = gpd.read_file('../../sources/UDS/Граф Иркутск_link_geojson.geojson').to_crs(epsg=4326)

# 4) Преобразуем треки в GeoDataFrame
gdf = gpd.GeoDataFrame(
    tracks,
    geometry=gpd.points_from_xy(tracks['lon'], tracks['lat']),
    crs="EPSG:4326"
)

# 5) Делаем единый мультилинейный объект всех дорог
roads_union = UDS.geometry.union_all()

# 6) Привязываем (snap) каждую точку к дороге
snapped = [
    nearest_points(pt, roads_union)[1]
    for pt in gdf.geometry
]
# присваиваем обратно
gdf['snapped_geom'] = snapped

# 7) Готовим карту
center = [gdf['lat'].mean(), gdf['lon'].mean()]
m = folium.Map(location=center, zoom_start=12, tiles='OpenStreetMap')

# 8) Добавляем «сырую» сеть
folium.GeoJson(
    UDS,
    name='Сеть дорог',
    style_function=lambda f: {'color': 'blue', 'weight':2, 'opacity':0.6}
).add_to(m)

# 9) Цвета для UUID
uuid_colors = {
    uid: "#{:06x}".format(random.randint(0, 0xFFFFFF))
    for uid in gdf['uuid'].unique()
}

# 10) Рисуем «snap’нутые» точки
for _, row in gdf.iterrows():
    col = uuid_colors[row['uuid']]
    folium.CircleMarker(
        location=(row['snapped_geom'].y, row['snapped_geom'].x),
        radius=4,
        color=col,
        fill=True,
        fill_color=col,
        fill_opacity=0.8,
        popup=f"UUID: {row['uuid']}"
    ).add_to(m)

# 11) Легенда
legend = """<div style="
    position: fixed; bottom: 50px; left: 50px;
    background: white; padding: 10px; border:1px solid grey;
    z-index:9999; font-size:14px;
"><b>UUID → цвет</b><br>"""
for uid, c in uuid_colors.items():
    legend += f"<i style='background:{c};width:12px;height:12px;" \
              "display:inline-block;margin-right:5px;'></i>{uid}<br>"
legend += "</div>"
m.get_root().html.add_child(folium.Element(legend))

# 12) Контроллер слоёв и сохранение
folium.LayerControl().add_to(m)
m.save('map_transports.html')

webbrowser.open('map_transports.html')
print("Результат в map_transports.html")