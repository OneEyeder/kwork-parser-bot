import re
from config import KEYWORDS


def matches_keywords(order, keywords=None):
    """Проверяет, содержит ли заказ ключевые слова"""
    if keywords is None:
        keywords = KEYWORDS
    
    # Текст для поиска: заголовок + описание
    text = f"{order.get('title', '')} {order.get('description', '')}".lower()
    
    for keyword in keywords:
        if keyword.lower() in text:
            return True
    
    return False


def format_order_message(order):
    """Форматирует заказ для отправки в Telegram"""
    title = order.get('title', 'Без названия')
    price = order.get('price', 'Цена не указана')
    link = order.get('link', '')
    description = order.get('description', '')
    
    # Обрезаем описание если слишком длинное
    if len(description) > 300:
        description = description[:300] + '...'
    
    message = f"📢 <b>Новый заказ!</b>\n\n"
    message += f"📝 <b>{title}</b>\n"
    message += f"💰 {price}\n\n"
    
    if description:
        message += f"📄 {description}\n\n"
    
    message += f"🔗 <a href='{link}'>Открыть на kwork.ru</a>"
    
    return message
