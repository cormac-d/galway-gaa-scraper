from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.galwaygaa.ie/results/"

def extract_filters():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(TARGET_URL)
        page.wait_for_timeout(5000)
        
        # This looks for the search/filter area specifically
        filter_html = page.locator(".sportlomo-sp-search").inner_html()
        print(filter_html)
        
        browser.close()

if __name__ == "__main__":
    extract_filters()
