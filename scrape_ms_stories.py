#!/usr/bin/env python3
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def main():
    # 1) Configure headless Chrome
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")

    # In GitHub Actions ubuntu-latest:
    chrome_binary = "/usr/bin/chromium-browser"
    driver_path   = "/usr/bin/chromedriver"
    chrome_opts.binary_location = chrome_binary
    service = Service(driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_opts)

    try:
        # 2) Navigate and wait for the bootstrap data
        url = "https://www.microsoft.com/en-us/customers/search"
        driver.get(url)
        # wait up to 15s for the __NEXT_DATA__ script tag to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "script#\\_\\_NEXT_DATA\\_\\_"))
        )

        # 3) Grab and parse the HTML
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        payload = json.loads(script.string)

        # 4) Extract first 20 customer stories
        items = payload["props"]["pageProps"]["searchResults"]["items"][:20]
        rows = []
        for it in items:
            rows.append({
                "URL":               it.get("url", ""),
                "Title":             it.get("title", ""),
                "Executive Summary": it.get("summary", ""),
                "Story":             "",  # needs a second pass if you want full text
                "Company Name":      it.get("customerName", ""),
                "Products":          ", ".join(it.get("productNames", [])),
                "Industry":          it.get("industry", ""),
                "Region":            it.get("region", "")
            })

        # 5) Save to Excel
        df = pd.DataFrame(rows)
        out_path = "microsoft_customer_stories.xlsx"
        df.to_excel(out_path, index=False)
        print(f"✅ Saved {len(rows)} stories to {out_path}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
