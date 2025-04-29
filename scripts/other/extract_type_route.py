import argparse
import sys

import pandas as pd


def filter_transport_data(csv_file, vehicle_type, route=None):
    """
    Фильтрует данные по типу транспорта и маршруту

    Параметры:
        csv_file (str): Путь к CSV файлу
        vehicle_type (str): Тип транспорта (bus/minibus/tramway/trolleybus)
        route (str/int/None): Номер маршрута (опционально)

    Возвращает:
        DataFrame: Отфильтрованные данные
    """
    try:
        # Чтение CSV файла
        df = pd.read_csv(csv_file, low_memory=False)

        # Фильтрация по типу транспорта
        filtered = df[df['vehicle_type'].str.lower() == vehicle_type.lower()]

        # Дополнительная фильтрация по маршруту если указан
        if route is not None:
            filtered = filtered[filtered['route'].astype(str) == str(route)]

        return filtered

    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        return pd.DataFrame()


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Фильтрация данных транспорта')
    parser.add_argument('--vehicle-type', required=True,
                        choices=['bus', 'minibus', 'tramway', 'trolleybus'],
                        help='Тип транспорта для фильтрации')
    parser.add_argument('--route', help='Номер маршрута (опционально)')
    return parser.parse_args()


def main():
    """Основная функция для вызова из командной строки"""
    args = parse_arguments()

    # Фильтрация данных
    csv_path = "../../sources/geotracks_transports/december.csv"
    result = filter_transport_data(
        csv_file=csv_path,
        vehicle_type=args.vehicle_type,
        route=args.route
    )

    # Вывод результатов
    if not result.empty:
        print(f"Найдено записей: {len(result)}")

        # Сохранение в файл
        output_file = "../../sources/current_route/current_route.csv"
        result.to_csv(output_file, index=False, sep=';')
        print(f"Данные сохранены в {output_file}")
        sys.exit(0)  # Успешное завершение
    else:
        print("Данные не найдены", file=sys.stderr)
        sys.exit(1)  # Завершение с ошибкой


if __name__ == "__main__":
    main()