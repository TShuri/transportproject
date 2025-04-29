import pandas as pd
import folium
import random
import webbrowser

# Читаем и чистим данные
tracks = pd.read_csv('../../sources/current_route/current_route.csv', sep=';', low_memory=False)
tracks['lat'] = pd.to_numeric(tracks['lat'], errors='coerce')
tracks['lon'] = pd.to_numeric(tracks['lon'], errors='coerce')
tracks = tracks.dropna(subset=['lat', 'lon', 'uuid']).reset_index(drop=True)

# Преобразуем треки в GeoDataFrame (для удобства, хотя можно и без него)
gdf = pd.DataFrame(tracks)
center = [gdf['lat'].mean(), gdf['lon'].mean()]

# Создаем карту
m = folium.Map(location=center, zoom_start=12, tiles='OpenStreetMap')

# Генерируем уникальные цвета для каждого UUID
uuid_colors = {
    uid: "#{:06x}".format(random.randint(0, 0xFFFFFF))
    for uid in gdf['uuid'].unique()
}

# Рисуем точки треков
for _, row in gdf.iterrows():
    col = uuid_colors[row['uuid']]
    folium.CircleMarker(
        location=(row['lat'], row['lon']),
        radius=4,
        color=col,
        fill=True,
        fill_color=col,
        fill_opacity=0.8,
        popup=f"UUID: {row['uuid']}\nШирота: {row['lat']:.6f}\nДолгота: {row['lon']:.6f}"
    ).add_to(m)

legend_html = """
<div style="
    position: fixed; 
    bottom: 50px; 
    left: 50px;
    background: white; 
    padding: 10px; 
    border: 1px solid grey;
    z-index: 9999; 
    font-size: 14px;
">
    <b>UUID → цвет</b><br>
"""

for uid, c in uuid_colors.items():
    legend_html += f'<i style="background:{c}; width:12px; height:12px; display:inline-block; margin-right:5px;"></i>{uid}<br>'

legend_html += "</div>"
m.get_root().html.add_child(folium.Element(legend_html))

# Сохраняем и открываем карту
m.save('tracks_map.html')
webbrowser.open('tracks_map.html')
print("Результат в tracks_map.html")