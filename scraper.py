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
        
        # Wait for the search form to load
        page.wait_for_selector("#fdate", timeout=15000)
        
        # 1. Force the 'From Date' to March 1st, 2026 using JavaScript evaluation 
        # (This bypasses any datepicker popup calendar issues)
        print("Adjusting date filter back to March 1st...")
        page.evaluate('document.getElementById("fdate").value = "01-03-2026"')
        
        # 2. Click the search button
        page.locator('input[name="btn"]').first.click()
        
        # Give the server 5 seconds to query the 6+ months of data
        page.wait_for_timeout(5000)
        
        # Wait for the results tables to appear in the HTML
        page.wait_for_selector("ul.table-body.results", timeout=20000)
        print("Historical data loaded. Extracting matches...")
        
        # Locate every match row on the page
        match_rows = page.locator("ul.table-body.results").all()
        
        for row in match_rows:
            competition = row.get_attribute("data-compname")
            
            # Skip if it's a hurling match or if competition is missing
            if not competition or "hurling" in competition.lower():
                continue
            
            # Extract scores and prepend a hidden single quote to stop Excel date formatting
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
        
        # 'utf-8-sig' forces Excel to recognize Irish fadas properly
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
        print(f"Success! {len(df)} football matches saved to {csv_filename}")
    else:
        print("No football results found on the page.")

if __name__ == "__main__":
    scrape_galway_football_results()
