from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tabulate import tabulate

SELENIUM_URL = 'http://localhost:4444/wd/hub'

def open_page(driver, url):
    ret = []
    driver.get(url)
    driver.implicitly_wait(10)
    
    # Проверяем, есть ли заголовок
    driver.find_element(By.TAG_NAME, 'h1')
    
    for item in driver.find_elements(By.CLASS_NAME, 'want-card'):
        obj = {}
        obj['link'] = item.find_element(By.CSS_SELECTOR, 'h1 a').get_attribute('href')
        obj['h1'] = item.find_element(By.TAG_NAME, 'h1').text
        obj['price_main'] = item.find_element(By.CLASS_NAME, 'wants-card__header-right-block').text
        
        try:
            obj['price_sub'] = item.find_element(
                By.CLASS_NAME, 
                'wants-card__description-higher-price'
            ).text
        except NoSuchElementException:
            obj['price_sub'] = None
        
        ret.append(obj)
    
    next_page = len(driver.find_elements(By.CLASS_NAME, 'pagination__arrow--next')) > 0
    return ret, next_page

def main():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # браузер не будет открываться графически
    chrome_options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    for i in range(1, 100):
        url = f'https://kwork.ru/projects?page={i}'
        local_arr, next_page = open_page(driver, url)
        print(f'* {i}')
        print(tabulate(local_arr, headers='keys', tablefmt='psql'))
        
        if not next_page:
            break
    
    driver.quit()

if __name__ == '__main__':
    main()
