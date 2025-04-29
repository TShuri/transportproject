import os
import sys
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import subprocess


class AppConfig:
    """Конфигурация приложения"""
    ROUTES_JSON = './sources/geotracks_transports/routes/routes.json'
    SCRIPTS = {
        "Сохранение маршрута в csv": "scripts/other/extract_type_route.py",
        "Работа с транспортом": "scripts/transports_with_stops/transports_with_stops.py",
        "Работа с анкетами": "scripts/ankets/ankets_script.py",
        "УДС с сегментами по анкетам": "scripts/stats_ankets/show_low_segments.py"
    }
    VEHICLE_TYPES = ["bus", "minibus", "tramway", "trolleybus"]
    WINDOW_SIZE = "700x300"


class ScriptRunner:
    """Класс для управления запуском скриптов"""

    @staticmethod
    def run_save_route(vehicle_type, route=None):
        """Запуск скрипта для сохранения маршрута в csv"""
        script_path = AppConfig.SCRIPTS["Сохранение маршрута в csv"]
        try:
            args = [sys.executable, os.path.basename(script_path),
                    "--vehicle-type", vehicle_type]

            if route:
                args.extend(["--route", route])

            subprocess.run(args, check=True, cwd=os.path.dirname(script_path))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка запуска скрипта: {str(e)}")

    @staticmethod
    def run_transport_script():
        """Запуск скрипта для работы с транспортом"""
        script_path = AppConfig.SCRIPTS["Работа с транспортом"]

        try:
            subprocess.run([sys.executable, os.path.basename(script_path)],
                           check=True, cwd=os.path.dirname(script_path))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка запуска скрипта: {str(e)}")

    @staticmethod
    def run_ankets_script(path_gpx_file):
        """Запуск скрипта для работы с анкетами"""
        script_path = AppConfig.SCRIPTS["Работа с анкетами"]
        try:
            args = [sys.executable, os.path.basename(script_path),
                    "--gpx_file", path_gpx_file]
            subprocess.run(args, check=True, cwd=os.path.dirname(script_path))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка запуска скрипта: {str(e)}")

    @staticmethod
    def run_uds_segments_for_ankets_script():
        """Запуск скрипта для работы с анкетами"""
        script_path = AppConfig.SCRIPTS["УДС с сегментами по анкетам"]
        try:
            subprocess.run([sys.executable, os.path.basename(script_path)],
                           check=True, cwd=os.path.dirname(script_path))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка запуска скрипта: {str(e)}")


class MainWindow:
    """Главное окно приложения"""

    def __init__(self, root):
        self.root = root
        self.root.title("Лаунчер маршрутов")
        self.root.geometry(AppConfig.WINDOW_SIZE)

        self.setup_ui()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.create_transport_section(main_frame)
        self.create_ankets_section(main_frame)

    def create_transport_section(self, parent):
        """Создание секции с работой треками транспорта"""
        transport_frame = ttk.LabelFrame(parent, text="Работа с треками транспорта")
        transport_frame.pack(fill="x", pady=10)

        # Выбор типа транспорта
        ttk.Label(transport_frame, text="Тип транспорта:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.vehicle_type_var = tk.StringVar(value=AppConfig.VEHICLE_TYPES[0])
        ttk.Combobox(
            transport_frame,
            textvariable=self.vehicle_type_var,
            values=AppConfig.VEHICLE_TYPES,
            state="readonly"
        ).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Ввод номера маршрута
        ttk.Label(transport_frame, text="Номер маршрута:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.route_entry = ttk.Entry(transport_frame)
        self.route_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Кнопка для обработки транспорта
        ttk.Button(
            transport_frame,
            text="Обработать транспорт",
            command=self.process_route
        ).grid(row=1, column=2, padx=10, pady=5)

    def create_ankets_section(self, parent):
        """Создание секции работы с треками анкет"""
        ankets_frame = ttk.LabelFrame(parent, text="Работа с треками анкет")
        ankets_frame.pack(fill="x", pady=10)

        # Выбор файла анкеты
        ttk.Label(ankets_frame, text="Файл анкеты:").grid(row=1, column=0, sticky="w", padx=5, pady=5)

        # Фрейм для поля ввода и кнопки выбора файла
        file_frame = ttk.Frame(ankets_frame)
        file_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Поле для отображения пути к файлу
        self.file_entry = ttk.Entry(file_frame)
        self.file_entry.pack(side="left", fill="x", expand=True)

        # Кнопка выбора файла
        ttk.Button(
            file_frame,
            text="Выбрать...",
            command=self._select_anket_file
        ).pack(side="right", padx=(5, 0))

        # Кнопка для работы с анкетами
        ttk.Button(
            ankets_frame,
            text="Работа с анкетами",
            command=self.process_anket
        ).grid(row=2, column=1, padx=10, pady=5)

        # Кнопка для работы с анкетами
        ttk.Button(
            ankets_frame,
            text="УДС с сегментами по всем анкетам",
            command=ScriptRunner.run_uds_segments_for_ankets_script
        ).grid(row=2, column=2, padx=10, pady=5)

    def _select_anket_file(self):
        """Открытие диалога выбора файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл анкеты",
            filetypes=[(".gpx файлы", "*.gpx"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)

    def process_route(self):
        """Обработка нажатия кнопки для обработки маршрута"""
        vehicle_type = self.vehicle_type_var.get()
        route = self.route_entry.get().strip() or None

        if not vehicle_type:
            messagebox.showwarning("Предупреждение", "Выберите тип транспорта")
            return

        ScriptRunner.run_save_route(vehicle_type, route)
        ScriptRunner.run_transport_script()

    def process_anket(self):
        """Обработка нажатия кнопки для обработки маршрута"""
        gpx_file = self.file_entry.get()

        if not gpx_file:
            messagebox.showwarning("Предупреждение", "Выберите файл")
            return

        ScriptRunner.run_ankets_script(gpx_file)


def main():
    """Точка входа в приложение"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()