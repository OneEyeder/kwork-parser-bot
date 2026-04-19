# Конфигурация бота
import os

# Получите токен от @BotFather и вставьте сюда
# Или установите переменную окружения TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# ID чата/пользователя для отправки уведомлений
# Узнать свой ID: напишите боту @userinfobot
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'ВАШ_CHAT_ID')

# Ключевые слова для фильтрации (регистр не важен)
KEYWORDS = ['вёрстка', 'верстка', 'сайт', 'лендинг', 'landing', 'html', 'css', 'frontend']

# Интервал проверки (в секундах)
CHECK_INTERVAL = 90  # 1.5 минуты

# Файл для хранения ID уже отправленных заказов
SEEN_ORDERS_FILE = 'see_orderns.json'
