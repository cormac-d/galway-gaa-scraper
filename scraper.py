from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.galwaygaa.ie/results/"

def extract_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Go straight to the results page
        page.goto(TARGET_URL)
        
        # Wait 5 seconds to ensure any visual elements finish rendering
        page.wait_for_timeout(5000)
        
        # Print the raw HTML layout to the GitHub Actions terminal
        html_code = page.content()
        print(html_code)
        
        browser.close()

if __name__ == "__main__":
    extract_html()
