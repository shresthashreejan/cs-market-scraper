from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            page = browser.new_page()
            page.goto('https://skinflow.gg')
            page.get_by_role("navigation").get_by_role("link", name="Buy").click()
            page.locator('input[type="number"][min="0"][step=".01"][class*="appearance:textfield"]').fill('50')
            page.locator('input[type="number"][min="0"][step=".01"][class*="appearance:textfield"]').press('Enter')
            page.screenshot(path='debug.png')
            browser.close()
        except Exception as e:
            print(f"Exception occurred: {str(e)}")

if __name__ == "__main__":
    main()