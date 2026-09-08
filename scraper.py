from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime

# Target the Galway GAA Results page or the direct SportsLomo widget URL
TARGET_URL = "https://www.galwaygaa.ie/competitions/"

def scrape_galway_football_results():
    scraped_data = []

    with sync_playwright() as p:
        # Launch a hidden (headless) browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the page and wait for the SportsLomo JavaScript to load
        page.goto(TARGET_URL)
        page.wait_for_selector(".sportslomo-results-widget", timeout=15000)
        
        # Extract the match rows (Requires mapping live CSS classes)
        match_rows = page.locator(".match-row").all()
        
        for row in match_rows:
            # Filter logic: skip if the sport is hurling
            competition = row.locator(".comp-name").inner_text()
            if "hurling" in competition.lower():
                continue
                
            match_info = {
                "Date": row.locator(".match-date").inner_text(),
                "Age_Group": competition,
                "Home_Team": row.locator(".home-team").inner_text(),
                "Home_Score": row.locator(".home-score").inner_text(),
                "Away_Team": row.locator(".away-team").inner_text(),
                "Away_Score": row.locator(".away-score").inner_text(),
                "Status": row.locator(".match-status").inner_text(), # e.g., 'Played', 'Postponed'
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            scraped_data.append(match_info)
            
        browser.close()

    # Convert the raw data into a CSV file
    if scraped_data:
        df = pd.DataFrame(scraped_data)
        csv_filename = f"Galway_GAA_Football_Results_{datetime.now().strftime('%Y')}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"Success! {len(df)} matches saved to {csv_filename}")
    else:
        print("No results found. Check CSS selectors.")

if __name__ == "__main__":
    scrape_galway_football_results()
