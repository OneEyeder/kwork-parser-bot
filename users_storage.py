import json
import os

USERS_FILE = 'subscribed_users.json'


def load_subscribed_users():
    """Загружает множество ID подписанных пользователей"""
    if not os.path.exists(USERS_FILE):
        return set()
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data)
    except Exception as e:
        print(f"Ошибка загрузки пользователей: {e}")
        return set()


def save_subscribed_users(user_ids):
    """Сохраняет множество ID пользователей"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(user_ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения пользователей: {e}")


def add_subscribed_user(user_id):
    """Добавляет пользователя в список подписчиков"""
    users = load_subscribed_users()
    users.add(user_id)
    save_subscribed_users(users)


def remove_subscribed_user(user_id):
    """Удаляет пользователя из списка подписчиков"""
    users = load_subscribed_users()
    users.discard(user_id)
    save_subscribed_users(users)


def get_subscribed_users():
    """Возвращает список всех подписанных пользователей"""
    return list(load_subscribed_users())
