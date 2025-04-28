# 🚍 TransportProject

Проект для визуализации и анализа транспортных маршрутов и анкетных данных с помощью Python. Имеет графический лаунчер с кнопками для запуска отдельных скриптов.

---

## 📁 Структура проекта

```
transportproject/
│
├── main.py                       # Лаунчер с интерфейсом (Tkinter)
│
├── scripts/                      # Скрипты обработки
│   ├── ankets/
│   │   ├── ankets_script.py      # Обработка анкетных треков
│   │   └── map_ankets.html       # Сгенерированная карта анкет
│   │
│   └── transports/
│       ├── transports_script.py  # Обработка транспортных треков
│       └── map_transports.html   # Сгенерированная карта транспорта
│
├── sources/                      # Исходные данные
│   ├── geotracks_ankets/         # Геотреки по анкетам
│   ├── geotracks_transports/     # Геотреки по маршрутам
│   ├── other/                    # Прочие данные (например, route10.csv)
│   └── UDS/                      # Дорожная сеть (GeoJSON)
│
├── tests/                        # Тесты (опционально)
└── venv/                         # Виртуальное окружение
```

---

## 🚀 Как запустить

1. **Создать виртуальное окружение (если ещё нет):**

```bash
python -m venv venv
```

2. **Активировать окружение:**

- Windows:
  ```bash
  venv\Scripts\activate
  ```
- macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

3. **Установить зависимости:**

```bash
pip install -r requirements.txt
```

> Если файла `requirements.txt` нет:
```bash
pip install pandas geopandas folium shapely xlsx2csv
pip freeze > requirements.txt
```

4. **Запустить лаунчер:**

```bash
python main.py
```

---

## 🧩 Возможности

- 📍 **Работа с анкетами** — загружает геоданные, визуализирует маршруты, генерирует интерактивную карту.
- 🚌 **Работа с транспортом** — подгружает CSV с координатами, привязывает к дорожной сети и строит карту маршрутов.

---

## 🛠 Используемые библиотеки

- [`pandas`](https://pandas.pydata.org/)
- [`geopandas`](https://geopandas.org/)
- [`folium`](https://python-visualization.github.io/folium/)
- [`shapely`](https://shapely.readthedocs.io/)
- [`xlsx2csv`](https://github.com/dilshod/xlsx2csv)
- `tkinter` (встроен в Python)

---

## 📌 Примечания

- Файлы карт сохраняются как `map_*.html` рядом со скриптами.
- Пути к данным указаны относительно директории скрипта.
- Для работы с GeoJSON и shapefile необходима установка `geopandas` и его зависимостей (`fiona`, `pyproj`, `rtree` и т.д.).
