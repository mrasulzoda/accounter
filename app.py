from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import os

app = Flask(__name__)
CORS(app)

WAREHOUSE_FILE = 'warehouse.csv'
products = {}

def load_data():
    global products
    products = {}
    if os.path.exists(WAREHOUSE_FILE):
        with open(WAREHOUSE_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['Название'].strip()
                quantity = int(row['Количество'])
                products[name] = quantity

def save_data():
    try:
        with open(WAREHOUSE_FILE, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Название', 'Количество'])
            for name, quantity in products.items():
                writer.writerow([name, quantity])
        return True
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")
        return False

load_data()

@app.route('/products', methods=['GET'])
def get_all_products():
    """Получить все товары"""
    products_list = [{"name": name, "quantity": qty} for name, qty in products.items()]
    return jsonify({"products": products_list})

@app.route('/products/<string:name>', methods=['GET'])
def get_product(name):
    """Получить товар по названию"""
    if name in products:
        return jsonify({name: products[name]})
    return jsonify({"error": "Товар не найден"}), 404

@app.route('/products/search', methods=['GET'])
def search_products():
    """Поиск товаров по части названия"""
    query = request.args.get('q', '').lower()
    results = {name: qty for name, qty in products.items() if query in name.lower()}
    return jsonify(results)

@app.route('/products', methods=['POST'])
def add_product():
    """Добавление нового товара"""
    data = request.json
    name = data.get('name')
    quantity = int(data.get('quantity', 0))
    
    if not name:
        return jsonify({"error": "Название товара обязательно"}), 400
    
    if name in products:
        return jsonify({"error": "Товар уже существует"}), 400
    
    products[name] = quantity
    save_data()
    return jsonify({name: quantity}), 201

@app.route('/products/<string:name>', methods=['PUT'])
def update_product(name):
    """Обновление количества товара"""
    if name not in products:
        return jsonify({"error": "Товар не найден"}), 404
    
    data = request.json
    quantity = int(data.get('quantity', products[name]))
    products[name] = quantity
    save_data()
    return jsonify({name: quantity})

@app.route('/products/<string:name>', methods=['DELETE'])
def delete_product(name):
    """Удаление товара"""
    if name not in products:
        return jsonify({"error": "Товар не найден"}), 404
    del products[name]
    save_data()
    return jsonify({"message": f"Товар '{name}' удален"}), 200

@app.route('/products/export', methods=['GET'])
def export_products():
    """Экспорт всех товаров в CSV"""
    save_data()
    return jsonify({"message": f"Данные экспортированы в {WAREHOUSE_FILE}"}), 200

@app.route('/products/import', methods=['POST'])
def import_products():
    """Импорт товаров из CSV (заменяет текущие данные)"""
    if 'file' not in request.files:
        return jsonify({"error": "Файл не найден"}), 400
    file = request.files['file']
    try:
        reader = csv.DictReader(file.stream.read().decode('utf-8').splitlines())
        global products
        products = {row['Название'].strip(): int(row['Количество']) for row in reader}
        save_data()
        return jsonify({"message": "Данные импортированы"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port = 5002)

