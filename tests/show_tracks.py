from xlsx2csv import Xlsx2csv
import geopandas as gpd
import shapely.geometry as shp
import matplotlib.pyplot as plt

track_file = "../10track2.xlsx"
Xlsx2csv(track_file, outputencoding="utf-8").convert("tracks.csv")
tracks = gpd.pd.read_csv('../sources/other/tracks.csv')
tracks['geometry'] = tracks.apply(
    lambda row: shp.Point(row['lon'], row['lat']), axis=1
)
tracks = gpd.GeoDataFrame(tracks, geometry='geometry', crs='EPSG: 4326')
tracks = tracks.to_crs(epsg=3857)
uds_path = 'Иркутск_link'
UDS = gpd.read_file(f'{uds_path}.rar!{uds_path}.SHX')
UDS = UDS. to_crs(epsg=3857)
base = UDS. plot(edgecolor='blue')
tracks.plot(ax=base, edgecolor=' red')
plt.show()