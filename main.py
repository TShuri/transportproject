import os
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import subprocess


class AppConfig:
    """Конфигурация приложения"""
    ROUTES_JSON = './sources/geotracks_transports/routes/routes.json'
    SCRIPTS = {
        "Работа с анкетами": "scripts/ankets/ankets_script.py",
        "Работа с транспортом": "scripts/transports_with_stops/transports_with_stops.py",
        "Сохранение маршрута в csv": "scripts/other/extract_type_route.py"
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
    def run_ankets_script():
        """Запуск скрипта для работы с анкетами"""
        script_path = AppConfig.SCRIPTS["Работа с анкетами"]
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

        self.create_input_section(main_frame)
        self.create_buttons_section(main_frame)

    def create_input_section(self, parent):
        """Создание секции ввода параметров"""
        input_frame = ttk.LabelFrame(parent, text="Параметры поиска")
        input_frame.pack(fill="x", pady=10)

        # Выбор типа транспорта
        ttk.Label(input_frame, text="Тип транспорта:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.vehicle_type_var = tk.StringVar(value=AppConfig.VEHICLE_TYPES[0])
        ttk.Combobox(
            input_frame,
            textvariable=self.vehicle_type_var,
            values=AppConfig.VEHICLE_TYPES,
            state="readonly"
        ).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Ввод номера маршрута
        ttk.Label(input_frame, text="Номер маршрута:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.route_entry = ttk.Entry(input_frame)
        self.route_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

    def create_buttons_section(self, parent):
        """Создание секции кнопок"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(pady=20)

        # Кнопка для сохранения маршрута в csv
        ttk.Button(
            buttons_frame,
            text="Сохранить маршрут в csv",
            command=self.process_save_route
        ).pack(side="left", padx=10, pady=5)

        # Кнопка для обработки транспорта
        ttk.Button(
            buttons_frame,
            text="Обработать транспорт",
            command=ScriptRunner.run_transport_script
        ).pack(side="left", padx=10, pady=5)

        # Кнопка для работы с анкетами
        ttk.Button(
            buttons_frame,
            text="Работа с анкетами",
            command=ScriptRunner.run_ankets_script
        ).pack(side="left", padx=10, pady=5)

    def process_save_route(self):
        """Обработка нажатия кнопки для сохранения маршрута"""
        vehicle_type = self.vehicle_type_var.get()
        route = self.route_entry.get().strip() or None

        if not vehicle_type:
            messagebox.showwarning("Предупреждение", "Выберите тип транспорта")
            return

        ScriptRunner.run_save_route(vehicle_type, route)


def main():
    """Точка входа в приложение"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()