from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime, timedelta

TARGET_URL = "https://www.galwaygaa.ie/results/"

def scrape_galway_football_results():
    scraped_data = []
    
    # Generate 7-day date chunks from March 1st of current year to today
    current_year = datetime.now().year
    start_date = datetime(current_year, 3, 1)
    end_date = datetime.now()
    date_chunks = []
    
    current = start_date
    while current <= end_date:
        chunk_end = current + timedelta(days=7)
        if chunk_end > end_date:
            chunk_end = end_date
        date_chunks.append((current.strftime("%d-%m-%Y"), chunk_end.strftime("%d-%m-%Y")))
        current = chunk_end + timedelta(days=1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Loading Galway GAA Results Page...")
        page.goto(TARGET_URL)
        page.wait_for_selector("#fdate", timeout=15000)
        
        for fdate, tdate in date_chunks:
            print(f"Scraping matches from {fdate} to {tdate}...")
            
            # Clear old DOM elements before new search
            page.evaluate('document.querySelectorAll("ul.table-body.results").forEach(el => el.remove());')
            
            # Set dates and trigger change events
            page.evaluate(f'''() => {{
                document.querySelectorAll('[name="fdate"]').forEach(el => {{
                    el.value = '{fdate}';
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }});
                document.querySelectorAll('[name="tdate"]').forEach(el => {{
                    el.value = '{tdate}';
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }});
            }}''')
            
            page.locator('input[name="btn"]').first.click()
            
            try:
                page.wait_for_selector("ul.table-body.results", timeout=12000)
                page.wait_for_timeout(1500) 
            except Exception:
                print(f"No results found for period {fdate} to {tdate}.")
                continue
            
            match_rows = page.locator("ul.table-body.results").all()
            
            if not match_rows:
                continue
                
            for row in match_rows:
                competition = row.get_attribute("data-compname")
                
                # Exclude hurling
                if not competition or "hurling" in competition.lower():
                    continue
                
                raw_home_score = row.get_attribute("data-homescore")
                raw_away_score = row.get_attribute("data-awayscore")
                    
                match_info = {
                    "Date": row.get_attribute("data-date"),
                    "Time": row.get_attribute("data-time"),
                    "Competition": competition,
                    "Home_Team": row.get_attribute("data-hometeam"),
                    "Home_Score": f"'{raw_home_score}" if raw_home_score else "",
                    "Away_Score": f"'{raw_away_score}" if raw_away_score else "",
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
        
        # Remove duplicate records
        df.drop_duplicates(subset=['Date', 'Time', 'Home_Team', 'Away_Team'], inplace=True)
        
        csv_filename = f"Galway_GAA_Football_Full_Season_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
        print(f"Success! {len(df)} total football matches saved to {csv_filename}")
    else:
        print("No football results found on the page.")

if __name__ == "__main__":
    scrape_galway_football_results()
