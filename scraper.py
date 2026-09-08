from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime

TARGET_URL = "https://www.galwaygaa.ie/results/"

def scrape_galway_football_results():
    scraped_data = []

    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the page
        print("Loading Galway GAA Results Page...")
        page.goto(TARGET_URL)
        
        # Wait for the results tables to appear in the HTML
        page.wait_for_selector("ul.table-body.results", timeout=20000)
        print("Page loaded successfully. Extracting matches...")
        
        # Locate every match row on the page
        match_rows = page.locator("ul.table-body.results").all()
        
        for row in match_rows:
            # Extract data directly from the hidden HTML attributes
            competition = row.get_attribute("data-compname")
            
            # Skip if it's a hurling match or if competition is missing
            if not competition or "hurling" in competition.lower():
                continue
                
            match_info = {
                "Date": row.get_attribute("data-date"),
                "Time": row.get_attribute("data-time"),
                "Competition": competition,
                "Home_Team": row.get_attribute("data-hometeam"),
                "Home_Score": row.get_attribute("data-homescore"),
                "Away_Score": row.get_attribute("data-awayscore"),
                "Away_Team": row.get_attribute("data-awayteam"),
                "Venue": row.get_attribute("data-venue"),
                "Referee": row.get_attribute("data-referee"),
                "Match_Status": row.get_attribute("data-comment"),
                "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            scraped_data.append(match_info)
            
        browser.close()

    # Save to CSV
    if scraped_data:
        df = pd.DataFrame(scraped_data)
        csv_filename = f"Galway_GAA_Football_Results_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"Success! {len(df)} football matches saved to {csv_filename}")
    else:
        print("No football results found on the page.")

if __name__ == "__main__":
    scrape_galway_football_results()
