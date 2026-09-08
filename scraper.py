from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime

TARGET_URL = "https://www.galwaygaa.ie/results/"

def scrape_galway_football_results():
    scraped_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Loading Galway GAA Results Page...")
        page.goto(TARGET_URL)
        
        page.wait_for_selector("#fdate", timeout=15000)
        
        print("Bypassing datepicker and injecting March 1st...")
        # Inject the date into both visible and hidden fields, and force the site to recognize the change
        page.evaluate('''() => {
            document.querySelectorAll('[name="fdate"]').forEach(el => {
                el.value = '01-03-2026';
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('input', { bubbles: true }));
            });
        }''')
        
        # Click the search button
        page.locator('input[name="btn"]').first.click()
        
        # Give the server extra time (8 seconds) to query the massive half-year dataset
        page.wait_for_timeout(8000)
        
        page.wait_for_selector("ul.table-body.results", timeout=20000)
        print("Historical data loaded. Extracting matches...")
        
        match_rows = page.locator("ul.table-body.results").all()
        
        for row in match_rows:
            competition = row.get_attribute("data-compname")
            
            if not competition or "hurling" in competition.lower():
                continue
            
            raw_home_score = row.get_attribute("data-homescore")
            raw_away_score = row.get_attribute("data-awayscore")
            safe_home_score = f"'{raw_home_score}" if raw_home_score else ""
            safe_away_score = f"'{raw_away_score}" if raw_away_score else ""
                
            match_info = {
                "Date": row.get_attribute("data-date"),
                "Time": row.get_attribute("data-time"),
                "Competition": competition,
                "Home_Team": row.get_attribute("data-hometeam"),
                "Home_Score": safe_home_score,
                "Away_Score": safe_away_score,
                "Away_Team": row.get_attribute("data-awayteam"),
                "Venue": row.get_attribute("data-venue"),
                "Referee": row.get_attribute("data-referee"),
                "Match_Status": row.get_attribute("data-comment"),
                "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            scraped_data.append(match_info)
            
        browser.close()

    if scraped_data:
        df = pd.DataFrame(scraped_data)
        csv_filename = f"Galway_GAA_Football_Season_Results_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
        print(f"Success! {len(df)} football matches saved to {csv_filename}")
    else:
        print("No football results found on the page.")

if __name__ == "__main__":
    scrape_galway_football_results()
