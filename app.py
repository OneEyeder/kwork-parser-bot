"""
Telegram bot for kwork.ru parser
Deploy on Render.com
"""

import asyncio
import logging
import os
from datetime import datetime
from aiohttp import web

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command

from config import TELEGRAM_BOT_TOKEN, CHECK_INTERVAL, KEYWORDS
from parser import get_all_orders
from storage import load_seen_orders, add_seen_order
from filters import matches_keywords, format_order_message
from users_storage import add_subscribed_user, get_subscribed_users, load_subscribed_users

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Флаг для остановки мониторинга
monitoring_active = False
monitoring_task = None


# ===== WEB SERVER (минимальный для Render) =====

async def start_web_server():
    """Запускает минимальный веб-сервер (Render требует порт)"""
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text='Bot is running'))
    
    port = int(os.environ.get('PORT', 10000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Web server on port {port}")
    return runner


# ===== TELEGRAM BOT =====

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    global monitoring_active, monitoring_task
    
    chat_id = message.chat.id
    user_name = message.from_user.first_name if message.from_user else "Unknown"
    
    # Если токен не настроен
    if TELEGRAM_BOT_TOKEN == 'ВАШ_ТОКЕН_ЗДЕСЬ' or not TELEGRAM_BOT_TOKEN:
        await message.answer(
            "❌ <b>Бот не настроен!</b>\n\n"
            "Пожалуйста, установите TELEGRAM_BOT_TOKEN в переменных окружения"
        )
        return
    
    # Добавляем пользователя в список подписчиков
    add_subscribed_user(chat_id)
    
    if monitoring_active:
        await message.answer(
            f"👋 Привет, {user_name}!\n\n"
            f"✅ Мониторинг уже запущен!\n"
            f"Вы будете получать уведомления о новых заказах по ключевым словам.\n\n"
            f"📊 Статус: /status\n"
            f"🧪 Тест: /test"
        )
        return
    
    monitoring_active = True
    
    # Запускаем фоновую задачу мониторинга
    monitoring_task = asyncio.create_task(monitor_orders())
    
    await message.answer(
        f"🚀 <b>Мониторинг запущен!</b>\n\n"
        f"📊 Параметры:\n"
        f"• Интервал проверки: {CHECK_INTERVAL} секунд\n"
        f"• Ключевые слова: {', '.join(KEYWORDS)}\n\n"
        f"Бот будет проверять новые заказы и отправлять уведомления о подходящих.\n\n"
        f"Команды:\n"
        f"/stop - остановить мониторинг\n"
        f"/status - проверить статус\n"
        f"/test - тестовый запрос"
    )
    
    logger.info(f"Мониторинг запущен. Подписчиков: {len(load_subscribed_users())}")


@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    """Обработка команды /stop"""
    global monitoring_active, monitoring_task
    
    if not monitoring_active:
        await message.answer("❌ Мониторинг уже остановлен")
        return
    
    monitoring_active = False
    
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
        monitoring_task = None
    
    await message.answer("🛑 <b>Мониторинг остановлен</b>")
    logger.info("Мониторинг остановлен")


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Проверка статуса"""
    status = "🟢 Активен" if monitoring_active else "🔴 Остановлен"
    seen_count = len(load_seen_orders())
    subscribers_count = len(load_subscribed_users())
    
    await message.answer(
        f"📊 <b>Статус мониторинга</b>\n\n"
        f"Состояние: {status}\n"
        f"Интервал: {CHECK_INTERVAL} сек\n"
        f"Видено заказов: {seen_count}\n"
        f"Подписчиков: {subscribers_count}\n"
        f"Ключевые слова: {', '.join(KEYWORDS)}"
    )


@dp.message(Command("test"))
async def cmd_test(message: types.Message):
    """Тестовый запрос"""
    await message.answer("🔄 Выполняю тестовый запрос...")
    
    try:
        orders = get_all_orders(max_pages=1)
        matched = [o for o in orders if matches_keywords(o)]
        
        await message.answer(
            f"✅ <b>Тест выполнен!</b>\n\n"
            f"Найдено заказов: {len(orders)}\n"
            f"Подходящих по ключевым словам: {len(matched)}\n\n"
            f"Примеры подходящих заказов:"
        )
        
        # Показываем до 3 примеров
        for order in matched[:3]:
            msg = format_order_message(order)
            await message.answer(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
            
    except Exception as e:
        logger.error(f"Ошибка в тестовом запросе: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("keywords"))
async def cmd_keywords(message: types.Message):
    """Показать текущие ключевые слова"""
    await message.answer(
        f"🔍 <b>Текущие ключевые слова:</b>\n\n"
        f"{', '.join(KEYWORDS)}\n\n"
        f"Для изменения отредактируйте файл <code>config.py</code>"
    )


async def check_and_notify():
    """Проверяет заказы и отправляет уведомления всем подписчикам"""
    logger.info("Начинаю проверку заказов...")
    
    # Получаем список подписчиков
    subscribers = get_subscribed_users()
    if not subscribers:
        logger.warning("Нет подписчиков для отправки уведомлений")
        return
    
    try:
        # Получаем заказы (только с первой страницы - самые новые)
        orders = get_all_orders(max_pages=1)
        seen_orders = load_seen_orders()
        
        new_orders = []
        matched_orders = []
        
        for order in orders:
            order_id = order.get('id')
            
            # Пропускаем уже виденные
            if order_id in seen_orders:
                continue
            
            new_orders.append(order)
            
            # Проверяем ключевые слова
            if matches_keywords(order):
                matched_orders.append(order)
                logger.info(f"Найден подходящий заказ: {order.get('title')}")
            
            # Добавляем в список виденных
            add_seen_order(order_id)
        
        logger.info(f"Новых заказов: {len(new_orders)}, Подходящих: {len(matched_orders)}, Подписчиков: {len(subscribers)}")
        
        # Отправляем уведомления всем подписчикам
        for order in matched_orders:
            msg = format_order_message(order)
            
            for chat_id in subscribers:
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=msg,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False
                    )
                    # Небольшая задержка между сообщениями
                    await asyncio.sleep(0.3)
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения пользователю {chat_id}: {e}")
        
        # Отправляем сводку если были новые заказы
        if new_orders and matched_orders:
            summary = (
                f"📊 <b>Проверка {datetime.now().strftime('%H:%M:%S')}</b>\n"
                f"Новых: {len(new_orders)} | "
                f"Подходящих: {len(matched_orders)}"
            )
            logger.info(summary)
                
    except Exception as e:
        logger.error(f"Ошибка при проверке заказов: {e}")


async def monitor_orders():
    """Фоновая задача мониторинга"""
    logger.info("Запущен мониторинг для всех подписчиков")
    
    while monitoring_active:
        try:
            await check_and_notify()
        except Exception as e:
            logger.error(f"Ошибка в цикле мониторинга: {e}")
        
        # Ждём до следующей проверки
        await asyncio.sleep(CHECK_INTERVAL)
    
    logger.info("Мониторинг завершён")


async def start_bot():
    """Запускает Telegram бота"""
    logger.info("Запуск бота...")
    
    # Удаляем вебхук и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем polling в фоне
    polling_task = asyncio.create_task(dp.start_polling(bot))
    logger.info("Bot polling started")
    
    return polling_task


async def main():
    """Главная функция"""
    web_runner = await start_web_server()
    bot_task = await start_bot()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Shutting down...")
    finally:
        await web_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Server stopped")
