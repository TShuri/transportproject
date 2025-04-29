from xlsx2csv import Xlsx2csv

path = '../../sources/geotracks_transports/'
track_file = f'{path}ДЕКАБРЬ.xlsx'
Xlsx2csv(track_file, outputencoding="utf-8").convert(f"{path}december.csv")