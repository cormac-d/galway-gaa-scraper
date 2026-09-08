from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.galwaygaa.ie/results/"

def find_filters():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(TARGET_URL)
        page.wait_for_timeout(5000)
        
        # Grab the HTML of every input, dropdown, and button on the page
        elements = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('input, select, button'))
                        .map(el => el.outerHTML);
        }''')
        
        for el in elements:
            print(el)
            
        browser.close()

if __name__ == "__main__":
    find_filters()
