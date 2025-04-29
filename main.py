import os
import sys
import tkinter as tk
import subprocess

# Здесь кнопки и пути к скриптам
scripts = {
    "Работа с анкетами": "scripts/ankets/ankets_script.py",
    "Работа с транспортом": "scripts/transports/transports_script.py",
    "Работа с транспортом и остановками": "scripts/transports/map_tracks_with_stops.py"
}

def run_script(path):
    try:
        script_dir = os.path.dirname(path)
        script_name = os.path.basename(path)

        subprocess.run(
            [sys.executable, script_name],
            check=True,
            cwd=script_dir  # ← поменяли рабочую директорию
        )
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске {path}: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")


def main():
    root = tk.Tk()
    root.title("Лаунчер")

    for name, path in scripts.items():
        tk.Button(
            root,
            text=name,
            width=30,
            height=2,
            command=lambda p=path: run_script(p)
        ).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
