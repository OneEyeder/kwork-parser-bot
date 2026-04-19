from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_driver():
    """Создаёт и возвращает настроенный драйвер Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    return webdriver.Chrome(options=chrome_options)


def parse_orders(driver, page=1):
    """Парсит заказы с указанной страницы kwork.ru"""
    url = f'https://kwork.ru/projects?page={page}'
    orders = []
    
    try:
        driver.get(url)
        driver.implicitly_wait(10)
        
        # Проверяем наличие заголовка
        driver.find_element(By.TAG_NAME, 'h1')
        
        cards = driver.find_elements(By.CLASS_NAME, 'want-card')
        logger.info(f"Найдено {len(cards)} карточек на странице {page}")
        
        for item in cards:
            try:
                order = {}
                
                # Ссылка и ID заказа
                link_elem = item.find_element(By.CSS_SELECTOR, 'h1 a')
                order['link'] = link_elem.get_attribute('href')
                # Извлекаем ID из URL (например, https://kwork.ru/projects/1234567)
                order_id = order['link'].split('/')[-1].split('?')[0]
                order['id'] = order_id
                
                # Заголовок
                order['title'] = item.find_element(By.TAG_NAME, 'h1').text.strip()
                
                # Цена
                order['price'] = item.find_element(
                    By.CLASS_NAME, 'wants-card__header-right-block'
                ).text.strip()
                
                # Описание (если есть)
                try:
                    desc = item.find_element(
                        By.CLASS_NAME, 'wants-card__description-text'
                    ).text.strip()
                    order['description'] = desc
                except NoSuchElementException:
                    order['description'] = ''
                
                # Альтернативная цена (если есть)
                try:
                    order['price_alt'] = item.find_element(
                        By.CLASS_NAME, 'wants-card__description-higher-price'
                    ).text.strip()
                except NoSuchElementException:
                    order['price_alt'] = None
                
                orders.append(order)
                
            except Exception as e:
                logger.warning(f"Ошибка при парсинге карточки: {e}")
                continue
        
        # Проверка наличия следующей страницы
        has_next = len(driver.find_elements(By.CLASS_NAME, 'pagination__arrow--next')) > 0
        
    except WebDriverException as e:
        logger.error(f"Ошибка WebDriver: {e}")
        has_next = False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        has_next = False
    
    return orders, has_next


def get_all_orders(max_pages=3):
    """Получает заказы с первых max_pages страниц"""
    driver = None
    all_orders = []
    
    try:
        driver = get_driver()
        
        for page in range(1, max_pages + 1):
            orders, has_next = parse_orders(driver, page)
            all_orders.extend(orders)
            
            if not has_next:
                logger.info(f"Страница {page} последняя")
                break
                
        logger.info(f"Всего собрано {len(all_orders)} заказов")
        
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
    finally:
        if driver:
            driver.quit()
    
    return all_orders
