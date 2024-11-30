import sqlite3
import threading
from flask import Flask, jsonify
import tkinter as tk
from tkinter import ttk
import requests

# --- Flask сервер ---
app = Flask(__name__)

def get_db_connection():
    connection = sqlite3.connect("cars.db")
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/cars', methods=['GET'])
def get_cars():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            cars.id, 
            manufacturers.name AS manufacturer, 
            models.name AS model, 
            cars.year, 
            cars.price, 
            cars.color
        FROM cars
        JOIN models ON cars.model_id = models.id
        JOIN manufacturers ON models.manufacturer_id = manufacturers.id
    """)
    cars = cursor.fetchall()
    connection.close()
    return jsonify([dict(car) for car in cars])

def run_server():
    app.run(debug=False, use_reloader=False)

# --- Инициализация базы данных ---
def init_database():
    connection = sqlite3.connect("cars.db")
    cursor = connection.cursor()

    # Удаление таблиц, если они уже существуют
    cursor.execute("DROP TABLE IF EXISTS cars")
    cursor.execute("DROP TABLE IF EXISTS models")
    cursor.execute("DROP TABLE IF EXISTS manufacturers")

    # Создание таблиц
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS manufacturers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        manufacturer_id INTEGER NOT NULL,
        FOREIGN KEY (manufacturer_id) REFERENCES manufacturers (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        price REAL NOT NULL,
        color TEXT,
        FOREIGN KEY (model_id) REFERENCES models (id)
    )
    """)

    # Наполнение базы данных информацией
    manufacturers = [("Toyota",), ("BMW",), ("Tesla",)]
    models = [
        ("Corolla", 1),
        ("Camry", 1),
        ("Model S", 3),
        ("Model 3", 3),
        ("3 Series", 2),
        ("5 Series", 2)
    ]
    cars = [
        (1, 2020, 20000, "Red"),
        (2, 2021, 25000, "Blue"),
        (3, 2022, 50000, "White"),
        (4, 2023, 45000, "Black"),
        (5, 2019, 30000, "Silver"),
        (6, 2020, 35000, "Gray")
    ]

    cursor.executemany("INSERT OR IGNORE INTO manufacturers (name) VALUES (?)", manufacturers)
    cursor.executemany("INSERT OR IGNORE INTO models (name, manufacturer_id) VALUES (?, ?)", models)
    cursor.executemany("INSERT OR IGNORE INTO cars (model_id, year, price, color) VALUES (?, ?, ?, ?)", cars)

    connection.commit()
    connection.close()

# --- Клиентское приложение с tkinter ---
def fetch_cars():
    try:
        response = requests.get("http://127.0.0.1:5000/cars")
        response.raise_for_status()
        cars = response.json()
        for item in cars_tree.get_children():
            cars_tree.delete(item)
        for car in cars:
            cars_tree.insert('', 'end', values=(
                car['id'], car['manufacturer'], car['model'], car['year'], car['price'], car['color']
            ))
    except Exception as e:
        error_label.config(text=f"Error: {e}")

def start_gui():
    root = tk.Tk()
    root.title("Car Database Viewer")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    columns = ("ID", "Manufacturer", "Model", "Year", "Price", "Color")
    global cars_tree
    cars_tree = ttk.Treeview(frame, columns=columns, show='headings')
    for col in columns:
        cars_tree.heading(col, text=col)
    cars_tree.grid(row=0, column=0, columnspan=2)

    fetch_button = ttk.Button(frame, text="Fetch Cars", command=fetch_cars)
    fetch_button.grid(row=1, column=0, sticky=(tk.W))

    global error_label
    error_label = ttk.Label(frame, text="", foreground="red")
    error_label.grid(row=1, column=1, sticky=(tk.W))

    root.mainloop()

# --- Основной код ---
if __name__ == '__main__':
    # Инициализация базы данных
    init_database()

    # Запуск сервера в отдельном потоке
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Запуск клиентского интерфейса
    start_gui()
