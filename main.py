from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from datetime import datetime
import time
import re
import pandas as pd
import os

min_price = "100"
max_price = "500"

load_dotenv()
username = os.getenv('USERNAME')

float_to_abbr = {
    'Factory New': 'FN',
    'Minimal Wear': 'MW',
    'Field-Tested': 'FT',
    'Well-Worn': 'WW',
    'Battle-Scarred': 'BS'
}

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

def check_checkbox_state(csfloat, selector):
    input_checked_class = 'mdc-checkbox--selected'
    element = csfloat.query_selector(selector)
    classes = element.get_attribute('class')
    if input_checked_class in classes.split():
        return True
    else:
        return False

def main():
    data = []
    with sync_playwright() as p:
        try:
            user_data_dir = f'/home/{username}/.config/chromium/Default'
            browser = p.chromium.launch_persistent_context(user_data_dir=user_data_dir, headless=False, slow_mo=10)
            page = browser.new_page()
            page.goto('https://skinflow.gg')
            page.get_by_role("navigation").get_by_role("link", name="Buy").click()
            page.locator('input[type="number"][min="0"][step=".01"][class*="appearance:textfield"]').fill(min_price)
            page.locator('input[type="number"][min="0"][step=".01"][class*="appearance:textfield"]').press('Enter')
            page.locator('label.duration-50:nth-child(3) > input:nth-child(1)').fill(max_price)
            page.locator('label.duration-50:nth-child(3) > input:nth-child(1)').press('Enter')
            page.locator('div.gap-2:nth-child(5) > button:nth-child(1)').click()
            page.locator('div.hover\:bg-white\/10:nth-child(2) > input:nth-child(1)').click()
            page.locator('div.hover\:bg-white\/10:nth-child(2) > input:nth-child(1)').click()

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
                            'SKINFLOW_PRICE': price,
                            'CSFLOAT_PRICE': '',
                            '%': ''
                        })
                page.mouse.click(x=0, y=0)

            csfloat = browser.new_page()
            csfloat.goto('https://csfloat.com/search?sort_by=lowest_price&type=buy_now')
            csfloat.mouse.click(x=0, y=0)
            csfloat.mouse.click(x=0, y=0)
            for item in data:
                csfloat.locator('body > app-root > div > div.content > app-market-search > app-search > app-filter-content-container > div > div.content > div > div > app-search-bar > div > div.filter-btn > button > span.mat-mdc-button-touch-target').click()
                csfloat.locator('#mat-input-11').fill('')
                csfloat.locator('#mat-input-11').type(item['NAME'])
                csfloat.locator('#mat-input-11').press('Enter')

                if item['STATTRAK'] == 'Yes':
                    stattrak_selector = '#mat-mdc-checkbox-4-input'
                    is_checked = check_checkbox_state(csfloat, stattrak_selector)
                    if not is_checked:
                        csfloat.locator(stattrak_selector).click()
                if item['STATTRAK'] == 'No':
                    normal_selector = '#mat-mdc-checkbox-6-input'
                    is_checked = check_checkbox_state(csfloat, normal_selector)
                    if not is_checked:
                        csfloat.locator(normal_selector).click()

                wear_val = item['WEAR']
                if wear_val in float_to_abbr:
                    abbr = float_to_abbr[wear_val]
                    float_element = csfloat.get_by_role("complementary").get_by_text(abbr)
                    float_element.click()
                csfloat.mouse.click(x=500, y=500)
                time.sleep(2)
                price_selector = 'item-card.flex-item:nth-child(1) > mat-card:nth-child(1) > div:nth-child(1) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1)'
                try:
                    csfloat.wait_for_selector(price_selector, state='visible', timeout=5000)
                    card = csfloat.query_selector(price_selector)
                    if card:
                        csfloat_price = card.inner_text()
                        if csfloat_price:
                            sale_price = csfloat_price.replace(',', '')
                            sale_price = sale_price.strip('$')
                            sale_price = float(sale_price.strip())
                            sale_price = sale_price * 0.98
                            item['CSFLOAT_PRICE'] = sale_price
                            cost_price = item['SKINFLOW_PRICE'].replace(',', '')
                            cost_price = cost_price.strip('$')
                            cost_price = float(cost_price.strip())
                            percentage_difference = (sale_price - cost_price)/cost_price
                            item['%'] = round(percentage_difference * 100, 4)
                except Exception as e:
                    print(f"Skipping iteration for {item['NAME']}.")

                print(f"{item['NAME']} {item['WEAR']} {item['FLOAT']} {item['STATTRAK']} {item['SKINFLOW_PRICE']} {item['CSFLOAT_PRICE']} {item['%']}")

            timestamp = datetime.now().strftime('%m-%d')
            name = timestamp + " " + min_price + "-" + max_price
            filename = f'{name}.csv'
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            browser.close()
        except Exception as e:
            print(f"Exception occurred: {str(e)}")

if __name__ == "__main__":
    main()