from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import time
import re
import pandas as pd
import os

load_dotenv()
username = os.getenv('USERNAME')

def load_all_cards(page):
    duration = 20
    start_time = time.time()

    while time.time() - start_time < duration:
        page.evaluate("""
            var div = document.querySelector('#tradeItems');
            if (div) {
                div.scrollTop += 100;
            }
        """, '#tradeItems')
        time.sleep(0.1)

def clean_name(item_name):
    stattrak = 'No'

    if '★' in item_name:
        item_name = item_name.replace('★', '').strip()

    if 'StatTrak™' in item_name:
        stattrak = 'Yes'
        item_name = item_name.replace('StatTrak™', '').strip()

    match = re.search(r'\s*\(([^)]*)\)$', item_name)
    if match:
        wear = match.group(1)
        item_name = item_name[:match.start()].strip()
    else:
        wear = ''

    return item_name, stattrak, wear

def main():
    data = []
    with sync_playwright() as p:
        try:
            user_data_dir = f'/home/{username}/.config/chromium/Default'
            browser = p.chromium.launch_persistent_context(user_data_dir=user_data_dir, headless=False, slow_mo=10)
            page = browser.new_page()
            page.goto('https://skinflow.gg')
            page.get_by_role("navigation").get_by_role("link", name="Buy").click()
            page.locator('input[type="number"][min="0"][step=".01"][class*="appearance:textfield"]').fill('50')
            page.locator('input[type="number"][min="0"][step=".01"][class*="appearance:textfield"]').press('Enter')

            load_all_cards(page)

            tradeitems_selector = '#tradeItems .tradeItem'
            page.wait_for_selector(tradeitems_selector, state='visible', timeout=5000)

            tradeitems = page.query_selector_all(tradeitems_selector)
            for item in tradeitems:
                item.click(button='right')
                button = page.get_by_role("button", name="ADD TO CART")
                if button.is_visible():
                    price_element = item.query_selector('p.font-normal.text-md.text-white\\/80.leading-\\[20px\\]')
                    if price_element:
                        item_name = page.query_selector('p.inline.font-bold').text_content()
                        name, stattrak, wear = clean_name(item_name)
                        price = price_element.text_content().strip()
                        float_element = item.query_selector('div.flex.w-full.justify-between.px-3 > p > span')
                        if float_element:
                            float_value = float_element.text_content()
                        else:
                            float_value = ''

                        data.append({
                            'NAME': name,
                            'WEAR': wear,
                            'FLOAT': float_value,
                            'STATTRAK': stattrak,
                            'SKINFLOW_PRICE': price
                        })

                        print(f"NAME: {name} WEAR: {wear} FLOAT: {float_value} STATTRAK: {stattrak} SKINFLOW_PRICE: {price}")
                page.mouse.click(x=0, y=0)

            csfloat = browser.new_page()
            csfloat.goto('https://csfloat.com/search?sort_by=lowest_price&type=buy_now')
            csfloat.mouse.click(x=0, y=0)
            csfloat.mouse.click(x=0, y=0)
            for item in data:
                csfloat.locator('body > app-root > div > div.content > app-market-search > app-search > app-filter-content-container > div > div.content > div > div > app-search-bar > div > div.filter-btn > button > span.mat-mdc-button-touch-target').click()
                csfloat.locator('#mat-input-11').type(item['NAME'])
                csfloat.locator('#mat-input-11').press('Enter')
            csfloat.screenshot(path='debug.png')

            df = pd.DataFrame(data)
            df.to_csv('csdata.csv', index=False)
            browser.close()
        except Exception as e:
            print(f"Exception occurred: {str(e)}")

if __name__ == "__main__":
    main()