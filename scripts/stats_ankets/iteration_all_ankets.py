import json
import os
from find_low_speed_segments import analyze_and_append_low_speed_segments


def clear_geojson_file(file_path):
    """Очищает GeoJSON файл, оставляя только базовую структуру"""
    empty_geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(empty_geojson, f, ensure_ascii=False, indent=4)
    print(f"Файл {file_path} очищен")

def process_gpx_directory(root_dir, output_geojson):
    """
    Рекурсивно обрабатывает все GPX файлы в директории и её поддиректориях

    Параметры:
        root_dir (str): Корневая директория для поиска GPX файлов
        output_geojson (str): Путь к выходному GeoJSON файлу
    """
    # Очищаем выходной файл перед началом обработки
    if os.path.exists(output_geojson):
        clear_geojson_file(output_geojson)
    else:
        # Создаем пустой файл, если его нет
        with open(output_geojson, 'w', encoding='utf-8') as f:
            json.dump({
                "type": "FeatureCollection",
                "features": []
            }, f, ensure_ascii=False, indent=4)

    total_files = 0
    total_segments = 0

    # Рекурсивный обход директории
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith('.gpx'):
                gpx_path = os.path.join(root, file)
                try:
                    # Обработка каждого GPX файла
                    result = analyze_and_append_low_speed_segments(gpx_path, output_geojson)
                    total_files += 1
                    total_segments += result['low_speed_segments_count']

                    print(f"Обработан: {gpx_path}")
                    print(f"  Добавлено сегментов: {result['low_speed_segments_count']}")
                    print(f"  Средняя скорость: {result['avg_speed']:.1f} км/ч")
                except Exception as e:
                    print(f"Ошибка при обработке {gpx_path}: {str(e)}")

    # Итоговая статистика
    print("\n=== Итоговая статистика ===")
    print(f"Всего обработано GPX файлов: {total_files}")
    print(f"Всего добавлено сегментов: {total_segments}")
    print(f"Итоговый файл: {output_geojson}")


if __name__ == "__main__":
    # Укажите корневую директорию для поиска GPX файлов
    root_directory = "../../sources/geotracks_ankets/"

    # Укажите путь к выходному GeoJSON файлу
    output_geojson_file = "../../sources/stats_ankets/low_speed_segments.geojson"

    # Запуск обработки
    process_gpx_directory(root_directory, output_geojson_file)