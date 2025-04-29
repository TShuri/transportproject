import pandas as pd
import json

# Чтение CSV файла
df = pd.read_csv('../../sources/geotracks_transports/december.csv', low_memory=False)

# Извлечение уникальных пар "тип транспорта - маршрут"
unique_pairs = df[['vehicle_type', 'route']].drop_duplicates()

# Создание словаря в нужном формате
result = {}
for _, row in unique_pairs.iterrows():
    vehicle_type = row['vehicle_type']
    route = row['route']
    if vehicle_type not in result:
        result[vehicle_type] = []
    result[vehicle_type].append(route)

# Сохранение в JSON
with open('../../sources/other/routes.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("Данные сохранены в routes.json")