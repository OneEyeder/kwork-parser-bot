import json
import os
from config import SEEN_ORDERS_FILE


def load_seen_orders():
    """Загружает множество ID уже виденных заказов"""
    if not os.path.exists(SEEN_ORDERS_FILE):
        return set()
    
    try:
        with open(SEEN_ORDERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data)
    except Exception as e:
        print(f"Ошибка загрузки seen_orders: {e}")
        return set()


def save_seen_orders(order_ids):
    """Сохраняет множество ID заказов"""
    try:
        with open(SEEN_ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(order_ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения seen_orders: {e}")


def add_seen_order(order_id):
    """Добавляет один ID в список виденных"""
    seen = load_seen_orders()
    seen.add(order_id)
    save_seen_orders(seen)
