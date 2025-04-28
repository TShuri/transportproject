import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point  # Изменили импорт


def showGrafGeoJson():
    # Загрузка графа из GeoJSON
    gdf = gpd.read_file('Граф Иркутск_link_geojson.geojson')

    # Загрузка трека из CSV
    track_df = pd.read_csv(
        'tracks.csv',
        usecols=[0, 1],
        names=['lat', 'lon'],
        skiprows=1
    )

    # Создание геометрии ТОЧЕК
    geometry = [Point(lon, lat) for lon, lat in zip(track_df['lon'], track_df['lat'])]

    # Создание GeoDataFrame
    track_gdf = gpd.GeoDataFrame(
        geometry=geometry,  # Передаем список точек
        crs=gdf.crs  # Берем CRS из графа
    )

    # Визуализация
    fig, ax = plt.subplots(figsize=(10, 10))

    # Граф
    gdf.plot(ax=ax, color='gray', linewidth=0.5, label='Улично-дорожная сеть')

    # Точки трека
    track_gdf.plot(
        ax=ax,
        color='red',
        markersize=20,
        marker='o',
        edgecolor='black',
        label='Точки трека'
    )

    plt.title("Граф УДС с точками трека транспорта")
    plt.xlabel("Долгота")
    plt.ylabel("Широта")
    plt.legend()
    plt.show()


showGrafGeoJson()