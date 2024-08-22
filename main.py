from playwright.sync_api import sync_playwright
import time
import re

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

def clean_item_name(item_name):
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
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=False, slow_mo=10)
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
                        cleaned_name, stattrak, wear = clean_item_name(item_name)
                        price_text = price_element.text_content().strip()

                        float_element = item.query_selector('div.flex.w-full.justify-between.px-3 > p > span')
                        if float_element:
                            float_value = float_element.text_content()

                        print(f"NAME: {cleaned_name} WEAR: {wear} FLOAT: {float_value} STATTRAK: {stattrak} PRICE: {price_text}")
                page.mouse.click(x=0, y=0)

            page.screenshot(path='debug.png')
            browser.close()
        except Exception as e:
            print(f"Exception occurred: {str(e)}")

if __name__ == "__main__":
    main()